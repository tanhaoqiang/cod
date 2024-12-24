# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from pathlib import Path
from functools import cached_property
from contextlib import contextmanager
import json
from subprocess import check_call

from ninja.ninja_syntax import Writer as NinjaWriter

from .package import Package
from .repo import Repo
from .lock import Lock
from .thin import parse_armap
from .dep import get_symbol_deps

def get_obj_defs(symbols):
    defs = {}
    for name, obj in symbols:
        defs.setdefault(obj, set())
        defs[obj].add(name)
    return defs

class Workspace:

    def __init__(self, rootdir=None):
        self.rootdir = Path.cwd() if rootdir is None else Path(rootdir)
        self.workdir = self.rootdir / ".cod"

    def repodir(self, name):
        return self.workdir / f"repo.{name}"

    def builddir(self, profile_name):
        return self.workdir / f"profile.{profile_name}"

    @cached_property
    def top_package(self):
        return Package(self.rootdir)

    @cached_property
    def repos(self):
        return {
            name: Repo(self.rootdir, self.repodir(name), config)
            for name, config in self.top_package.manifest.repo.items()}

    @cached_property
    def lock(self):
        return Lock(self.rootdir / "cod.lock", self.repos)

    def write_build(self, profile_name):
        packages = [self.top_package]
        for pkgid, name in self.lock[profile_name]:
            packages.append(Package(self.repos[name].get_path(pkgid)))

        builddir = self.builddir(profile_name)
        builddir.mkdir(parents=True, exist_ok=True)

        includedirs = []
        for package in packages:
            includedirs.append(package.includedir.relative_to(builddir, walk_up=True))

        with (builddir / "build.ninja").open("w") as f:
            ninja = NinjaWriter(f)
            ninja.variable('python', [sys.executable])
            ninja.variable('zig', ["$python", "-mziglang"])
            ninja.variable('cc', ["$zig", "cc"])
            ninja.variable('ar', ["$zig", "ar"])
            ninja.rule('cc', ["$cc", "$cflags", "-MMD", "-MF", "$out.d", "-c", "$in", "-o", "$out"], depfile="$out.d")
            ninja.rule('ar', ["$python", "-mcod.ar", "$out", "$in"])
            ninja.rule('ld', ["$cc", "$in", "-o", "$out"])

            ninja.variable('cflags', [f"-I{d.as_posix()}" for d in includedirs])

            libs = []

            for package in packages:
                if not package.srcfiles:
                    continue
                objs = [
                    f'{package.id}/{path.with_suffix(".o").as_posix()}'
                    for path in package.srcfiles]
                for obj, path in zip(objs, package.srcfiles):
                    src = (package.srcdir / path).relative_to(builddir, walk_up=True).as_posix()
                    ninja.build([obj], "cc", [src])
                libname = f"lib/lib{package.id.name}.a"
                ninja.build([libname], "ar", objs)
                libs.append(libname)

            package = self.top_package
            objs = [
                f'obj/{path.with_suffix(".o").as_posix()}'
                for path in package.binfiles]
            for obj, path in zip(objs, package.binfiles):
                src = (package.bindir / path).relative_to(builddir, walk_up=True).as_posix()
                bin = f'bin/{path.with_suffix(".bin").as_posix()}'
                ninja.build([obj], "cc", [src])
                ninja.build([bin], "ld", [obj]+libs)
            ninja.build(['lib/bin.a'], "ar", objs)

        return libs

    def build(self, profile_name, no_bin=False):
        if self.top_package.includedeps:
            with self.lock(profile_name):
                self.lock.install_provides(self.top_package.includedeps)

        builddir = self.builddir(profile_name)

        libs = self.write_build(profile_name)
        if no_bin or not self.top_package.binfiles:
            if libs:
                builddir = self.builddir(profile_name)
                check_call([sys.executable, "-mninja"] + libs, cwd=builddir)
            return

        while True:
            check_call([sys.executable, "-mninja", "lib/bin.a"] + libs, cwd=builddir)
            bin_defs = get_obj_defs(parse_armap(builddir / "lib/bin.a"))
            symbols = dict(sum((parse_armap(builddir / lib) for lib in libs), []))
            lib_deps = {lib: get_symbol_deps(builddir, lib) for lib in set(symbols.values())}

            undefined = set()

            for obj, defs in bin_defs.items():
                queue = []
                queue.extend(get_symbol_deps(builddir, obj))
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
            libs = self.write_build(profile_name)

        check_call([sys.executable, "-mninja"], cwd=builddir)

    def install(self, profile_name, packages):
        with self.lock(profile_name):
            self.lock.install_packages(packages)

    def package(self):
        info = {
            "requires": self.top_package.includedeps,
            "provides": [f"<{h.as_posix()}>" for h in self.top_package.includefiles],
        }

        if self.top_package.srcfiles:
            self.build("release", no_bin=True)
            libname = f"lib{self.top_package.id.name}.a"
            symbols = parse_armap(self.builddir("release")/"lib"/libname)

            info["provides"].append(libname)
            info["provides"].extend(f"({s})" for s, _ in symbols)

        self.workdir.mkdir(parents=True, exist_ok=True)
        with (self.workdir / f"{self.top_package.id}.cod").open("w") as f:
            json.dump(info, f)
