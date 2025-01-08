# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from pathlib import Path
from functools import cached_property
from contextlib import contextmanager
import json
from subprocess import check_call
from platform import system, machine

from ninja.ninja_syntax import Writer as NinjaWriter

from .project import Project
from .package import Package, Profile
from .lock import Lock
from .thin import parse_armap
from .dep import get_symbol_deps

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
    return arch

class Workspace:

    def __init__(self, rootdir=None):
        self.rootdir = Path.cwd() if rootdir is None else Path(rootdir)
        self.workdir = self.rootdir / ".cod"

    def builddir(self, profile_name):
        return self.workdir / profile_name

    @cached_property
    def project(self):
        return Project(self.rootdir)

    @cached_property
    def top_package(self):
        return Package(self.rootdir)

    @cached_property
    def lock(self):
        return Lock(self.rootdir / "cod.lock", self.project.repos)

    def write_build(self, profile_name, top):
        arch = profile_name.rsplit('.', 1)[1]

        packages = [top]
        for pkgid, name in self.lock[profile_name]:
            packages.append(Profile(Package(self.project.repos[name].get_path(pkgid)), profile_name))

        builddir = self.builddir(profile_name)
        builddir.mkdir(parents=True, exist_ok=True)

        includedirs = []
        for package in packages:
            includedirs.extend(
                i.relative_to(builddir, walk_up=True)
                for i in package.includedirs)

        with (builddir / "build.ninja").open("w") as f:
            ninja = NinjaWriter(f)
            ninja.variable('python', [sys.executable])
            ninja.variable('zig', ["$python", "-mziglang"])
            ninja.variable('cc', ["$zig", "cc"])
            ninja.variable('ar', ["$zig", "ar"])
            ninja.rule('cc', ["$cc", "$cflags", "-MMD", "-MF", "$out.d", "-c", "$in", "-o", "$out"], depfile="$out.d")
            ninja.rule('ar', ["$python", "-mcod.ar", "$out", "$in"])
            ninja.rule('ld', ["$cc", "$cflags", "$in", "-o", "$out"])

            ninja.variable('cflags', [f"--target={arch}-freestanding"] + [f"-I{d.as_posix()}" for d in includedirs])

            libs = []

            for package in packages:
                if not package.objs:
                    continue
                objs = []
                for obj, path in package.objs.items():
                    obj = (str(package.id) / obj).as_posix()
                    objs.append(obj)
                    src = path.relative_to(builddir, walk_up=True).as_posix()
                    ninja.build([obj], "cc", [src])
                libname = f"lib/lib{package.id.name}.a"
                ninja.build([libname], "ar", objs)
                libs.append(libname)

            objs = []
            for bin, path in top.bins.items():
                src = path.relative_to(builddir, walk_up=True).as_posix()
                obj = ('obj' / bin.with_suffix(".o")).as_posix()
                objs.append(obj)
                bin = ('bin' / bin).as_posix()
                ninja.build([obj], "cc", [src])
                ninja.build([bin], "ld", [obj] + libs)

            ninja.build(['lib/bin.a'], "ar", objs)

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

        builddir = self.builddir(profile_name)

        libs = self.write_build(profile_name, top)
        if no_bin or not top.bins:
            if libs:
                check_call([sys.executable, "-mninja"] + libs, cwd=builddir)
            return

        while True:
            check_call([sys.executable, "-mninja", "lib/bin.a"] + libs, cwd=builddir)
            bin_defs = get_obj_defs(parse_armap(builddir / "lib/bin.a"))
            symbols = dict(sum((parse_armap(builddir / lib) for lib in libs), []))
            lib_deps = {lib: get_symbol_deps(builddir, arch, lib) for lib in set(symbols.values())}

            undefined = set()

            for obj, defs in bin_defs.items():
                queue = []
                queue.extend(get_symbol_deps(builddir, arch, obj))
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

        check_call([sys.executable, "-mninja"], cwd=builddir)

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
