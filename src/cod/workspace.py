# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from pathlib import Path
from functools import cached_property
import json
from subprocess import check_call
from platform import system, machine

from .project import Project
from .package import Package, Profile
from .lock import Lock
from .thin import parse_armap
from .dep import get_symbol_deps
from .ninja import NinjaWriter

def get_obj_defs(symbols):
    defs = {}
    for name, obj in symbols:
        defs.setdefault(obj, set())
        defs[obj].add(name)
    return defs

def get_native_arch():
    os = system()
    arch = machine()
    if os == 'Windows':
        if arch == 'AMD64':
            return 'x86_64'
    elif os == 'Darwin':
        if arch == 'arm64':
            return 'aarch64'
    return arch

class Workspace:

    def __init__(self, pkg_dir=None):
        self.pkg_dir = Path.cwd() if pkg_dir is None else Path(pkg_dir)
        self.workdir = self.pkg_dir / ".cod"

    def builddir(self, profile_name):
        return self.workdir / profile_name

    @cached_property
    def project(self):
        return Project(self.pkg_dir)

    @cached_property
    def top_package(self):
        return Package(self.pkg_dir)

    @cached_property
    def lock(self):
        return Lock(self.pkg_dir / "cod.lock", self.project.repos)

    def write_build(self, profile_name, top):
        arch = profile_name.rsplit('.', 1)[1]

        packages = [top]
        for pkgid, name in self.lock[profile_name]:
            packages.append(Profile(Package(self.project.repos[name].get_path(pkgid)), profile_name))

        rootdir = self.builddir(profile_name)
        rootdir.mkdir(parents=True, exist_ok=True)

        includedirs = []
        for package in packages:
            includedirs.extend(
                i.relative_to(rootdir, walk_up=True)
                for i in package.includedirs)

        with NinjaWriter(rootdir / "build.ninja") as ninja:
            ninja.variable('python', [sys.executable])
            ninja.variable('zig', ["$python", "-mziglang"])
            ninja.variable('cc', ["$zig", "cc"])
            ninja.variable('ar', ["$zig", "ar"])
            ninja.rule('cc', ["$cc", "$cflags", "-MMD", "-MF", "$out.d", "-c", "$in", "-o", "$out"], depfile="$out.d")
            ninja.rule('ar', ["$python", "-mcod.ar", "$out", "$in"])
            ninja.rule('ld', ["$cc", "$cflags", "$in", "$libs", "-o", "$out"])

            ninja.variable('cflags', [f"--target={arch}-freestanding"] + [f"-I{d.as_posix()}" for d in includedirs])

            libs = []
            for package in packages:
                if not package.objs:
                    continue
                lib_ninja = (rootdir/str(package.id)/"lib.ninja").relative_to(rootdir)
                libs.append(package.write_build_lib(rootdir, lib_ninja))
                ninja.subninja(lib_ninja.as_posix())

            ninja.variable('libs', libs)

            if top.bins:
                lib_ninja = (rootdir/"obj"/"lib.ninja").relative_to(rootdir)
                top.write_build_bin(rootdir, lib_ninja)
                ninja.subninja(lib_ninja.as_posix())

        return libs

    def build(self, arch, profile_name, no_bin=False):
        if arch is None:
            arch = get_native_arch()
        assert arch in (self.top_package.arch or (arch,))

        profile_name = f'{profile_name}.{arch}'
        top = Profile(self.top_package, profile_name)

        if top.includedeps:
            with self.lock(profile_name):
                self.lock.install_provides(top.includedeps)

        rootdir = self.builddir(profile_name)

        libs = self.write_build(profile_name, top)
        if no_bin or not top.bins:
            if libs:
                check_call([sys.executable, "-mninja"] + libs, cwd=rootdir)
            return

        while True:
            check_call([sys.executable, "-mninja", "lib/bin.a"] + libs, cwd=rootdir)
            bin_defs = get_obj_defs(parse_armap(rootdir / "lib/bin.a"))
            symbols = dict(sum((parse_armap(rootdir / lib) for lib in libs), []))
            lib_deps = {lib: get_symbol_deps(rootdir, arch, lib) for lib in set(symbols.values())}

            undefined = set()

            for obj, defs in bin_defs.items():
                queue = []
                queue.extend(get_symbol_deps(rootdir, arch, obj))
                while queue:
                    symbol = queue.pop(0)
                    if symbol in undefined:
                        continue
                    if symbol in defs:
                        continue
                    if symbol in symbols:
                        defs.add(symbol)
                        queue.extend(lib_deps[symbols[symbol]])
                    else:
                        undefined.add(symbol)

            if not undefined:
                break

            provides = {f"({s})" for s in undefined}
            with self.lock(profile_name):
                self.lock.install_provides(provides)
                if not self.lock.dirty:
                    break
            libs = self.write_build(profile_name, top)

        check_call([sys.executable, "-mninja"], cwd=rootdir)

    def install(self, arch, profile_name, packages):
        if arch is None:
            arch = get_native_arch()
        assert arch in (self.top_package.arch or (arch,))
        profile_name = f'{profile_name}.{arch}'
        with self.lock(profile_name):
            self.lock.install_packages(packages)

    def package(self, arch):
        if arch is None:
            for arch in self.top_package.arch or (get_native_arch(),):
                self.package(arch)
            return
        assert arch in (self.top_package.arch or (arch,))

        profile_name = f"release.{arch}"
        top = Profile(self.top_package, profile_name)
        info = {
            "requires": top.includedeps,
            "provides": [f"<{h.as_posix()}>" for h in top.includefiles],
        }

        if top.objs:
            self.build(arch, "release", no_bin=True)
            libname = f"lib{top.id.name}.a"
            symbols = parse_armap(self.builddir(profile_name)/"lib"/libname)
            info["provides"].append(libname)
            info["provides"].extend(f"({s})" for s, _ in symbols)

        self.workdir.mkdir(parents=True, exist_ok=True)
        with (self.workdir / f"{top.id}.cod").open("w") as f:
            json.dump(info, f)
