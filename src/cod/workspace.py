# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from pathlib import Path
import json
from subprocess import check_call
from platform import system, machine

from .project import Project
from .package import Package, Profile
from .lock import Lock
from .thin import parse_armap
from .dep import get_symbol_deps
from .ninja import NinjaWriter
from .compat import relative_to, cached_property

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
        elif arch == 'x86':
            from warnings import warn
            from importlib.metadata import version
            if version('ziglang') == '0.13.0':
                warn("zig 0.13.0 on x86-windows is broken, see https://github.com/ziglang/zig/issues/20047")
            return 'i686'
        elif arch == 'ARM64':
            return 'aarch64'
    elif os == 'Darwin':
        if arch == 'arm64':
            return 'aarch64'
    return arch

def arch_to_target(arch):
    if arch in ('i386', 'i486', 'i586', 'i686'):
        return ["--target=x86-freestanding-none", f"-mcpu={arch}"]
    return [f"--target={arch}-freestanding-none"]

LIB_PROFILE='release'

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
            packages.append(Profile(Package(self.project.repos[name].get_path(pkgid)), f'{LIB_PROFILE}.{arch}'))
        packages.sort()

        rootdir = self.builddir(profile_name)
        rootdir.mkdir(parents=True, exist_ok=True)

        includedirs = []
        for package in packages:
            includedirs.extend(relative_to(i, rootdir) for i in package.includedirs)

        with NinjaWriter(rootdir / "build.ninja") as ninja:
            ninja.variable('python', [sys.executable])
            ninja.variable('zig', ["$python", "-mziglang"])
            ninja.variable('cc', ["$zig", "clang", f"--target={arch}-unknown-unknown"])
            ninja.variable('ar', ["$zig", "ar"])
            ninja.rule('cc', ["$cc", "$cflags", "-MMD", "-MF", "$out.d", "-c", "$in", "-o", "$out"], depfile="$out.d", description="CC $out")
            ninja.rule('as', ["$cc", "$cflags", "$sflags", "-MMD", "-MF", "$out.d", "-c", "$in", "-o", "$out"], depfile="$out.d", description="AS $out")
            ninja.rule('ar', ["$python", "-mcod.ar", "$out", "$in"], description="AR $out")
            ninja.rule('objcopy', ["$python", "-mcod.objcopy", "$out", "$in"], description="OBJCOPY $out")
            ninja.variable('linker-script', 'linker-script')
            ninja.build(['linker-script'], "phony")
            target = arch_to_target(arch)
            ninja.rule('ld', ["$zig", "cc"] + target + ["$cflags", "$ldflags", "$linker-script-flags", "$in", "$libs", "-o", "$out"], description="LD $out")

            ninja.variable('cflags', ["-ffreestanding", "-nostdinc", "-nostdlib", "-fno-builtin"] + [f"-I{d}" for d in includedirs])

            for package in packages:
                lib_ninja = rootdir/str(package.id)/"export.ninja"
                with NinjaWriter(lib_ninja) as subninja:
                    package.write_build_export(rootdir, subninja)
                ninja.include(lib_ninja.relative_to(rootdir))

            libs = []
            for package in packages:
                if not package.objs:
                    continue
                lib_ninja = (rootdir/str(package.id)/"lib.ninja").relative_to(rootdir)
                libs.append(package.write_build_lib(rootdir, lib_ninja))
                ninja.subninja(lib_ninja.as_posix())
            ninja.build(['libs'], "phony", libs)
            ninja.variable('libs', libs)

            if top.elfs:
                lib_ninja = (rootdir/"obj"/"lib.ninja").relative_to(rootdir)
                top.write_build_bin(rootdir, lib_ninja)
                ninja.subninja(lib_ninja.as_posix())

        return libs

    def build(self, arch, profile_name, no_bin=False):
        if arch is None:
            arch = get_native_arch()
            if self.top_package.arch and len(self.top_package.arch) == 1:
                arch = self.top_package.arch[0]
        assert arch in (self.top_package.arch or (arch,))

        profile_name = f'{profile_name}.{arch}'
        top = Profile(self.top_package, profile_name)

        if top.includedeps:
            with self.lock(profile_name):
                self.lock.install_provides(top.includedeps)

        rootdir = self.builddir(profile_name)

        libs = self.write_build(profile_name, top)
        if no_bin or not top.elfs:
            if libs:
                check_call([sys.executable, "-mninja"] + libs, cwd=rootdir)
            return

        target = arch_to_target(arch)

        while True:
            check_call([sys.executable, "-mninja", "lib/bin.a"] + libs, cwd=rootdir)
            bin_defs = get_obj_defs(parse_armap(rootdir / "lib/bin.a"))
            symbols = dict(sum((parse_armap(rootdir / lib) for lib in libs), []))
            lib_deps = {lib: get_symbol_deps(rootdir, target, lib) for lib in set(symbols.values())}

            undefined = set()

            for obj, defs in bin_defs.items():
                queue = []
                queue.extend(get_symbol_deps(rootdir, target, obj))
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
            if self.top_package.arch and len(self.top_package.arch) == 1:
                arch = self.top_package.arch[0]
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

        profile_name = f"{LIB_PROFILE}.{arch}"
        top = Profile(self.top_package, profile_name)
        info = {
            "requires": top.includedeps,
            "provides": [f"<{h.as_posix()}>" for h in top.includefiles],
        }

        if top.export_flags.linker_script:
            info["provides"].append("linker-script")

        if top.objs:
            self.build(arch, LIB_PROFILE, no_bin=True)
            libname = f"lib{top.id.name}.a"
            symbols = parse_armap(self.builddir(profile_name)/"lib"/libname)
            info["provides"].append(libname)
            info["provides"].extend(f"({s})" for s, _ in symbols)

        self.workdir.mkdir(parents=True, exist_ok=True)
        with (self.workdir / f"{top.id}.cod").open("w") as f:
            json.dump(info, f)
