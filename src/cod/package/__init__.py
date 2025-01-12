# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass
from functools import cached_property
import tomllib

from ..dep import get_include_deps
from . import manifest
from ..ninja import NinjaWriter

@dataclass(frozen=True)
class EVR:
    epoch: int
    version: str
    release: str

    @classmethod
    def from_str(self, s):
        ev, release = s.rsplit("-", 1)
        ev = ev.split(":", 1)
        version = ev[-1]
        if len(ev) > 1:
            epoch = ev[0]
        else:
            epoch = 0
        return self(epoch, version, release)

    def __str__(self):
        if not self.epoch:
            return f"{self.version}-{self.release}"
        return f"{self.epoch}:{self.version}-{self.release}"

@dataclass(frozen=True)
class PackageId:
    name: str
    evr: str
    arch: str

    @classmethod
    def from_str(self, s):
        s, arch = s.rsplit(".", 1)
        name, ev, r = s.rsplit("-", 2)
        return self(name, f"{ev}-{r}", arch)

    @classmethod
    def from_solvable(self, s):
        return self(s.name, s.evr, s.arch)

    def __str__(self):
        return f"{self.name}-{self.evr}.{self.arch}"

def find_files(path, pattern, suffix, prefix="."):
    return {prefix / (f.relative_to(path).with_suffix(suffix)):f
            for f in path.rglob(pattern)}

class Package:

    def __init__(self, rootdir):
        self.rootdir = rootdir

        with (self.rootdir / "cod.toml").open("rb") as f:
            toml = tomllib.load(f)
        self.manifest = manifest.Manifest.model_validate(toml)
        package = self.manifest.package
        self.name = package.name
        self.evr = EVR(package.epoch, package.version, package.release)
        arch = package.arch
        if isinstance(arch, str):
            arch = [arch]
        self.arch = arch

def get_build_flags(build, arch):
    if isinstance(build, manifest.BuildFlags):
        return build.normalize()
    default = manifest.BuildFlags()
    return build.get('noarch', default) + build.get(arch, default)

class Profile:

    def __init__(self, package, profile_name):
        self.package = package
        profile_name, arch = profile_name.rsplit('.', 1)
        self.build_arch = arch
        if package.arch is None:
            arch = 'noarch'
        self.arch = arch
        self.manifest = self.package.manifest.profile.get(profile_name, manifest.Profile())
        self.id = PackageId(package.name, str(package.evr), arch)

        self.includedirs = [package.rootdir / "include"]
        if self.archdir:
            self.includedirs.append(self.archdir / "include")

    def __lt__(self, other):
        return str(self.id) < str(other.id)

    @cached_property
    def build_flags(self):
        package_flags = get_build_flags(self.package.manifest.build, self.build_arch)
        profile_flags = get_build_flags(self.manifest.build, self.build_arch)
        return package_flags + profile_flags

    @cached_property
    def export_flags(self):
        return get_build_flags(self.package.manifest.export, self.build_arch)

    @cached_property
    def archdir(self):
        if self.arch != 'noarch':
            return self.package.rootdir / "arch" / self.arch

    @cached_property
    def bins(self):
        d = find_files(self.package.rootdir / "bin", "*.c", ".bin")
        if self.archdir:
            d.update(find_files(self.archdir / "bin", "*.c", ".bin"))
        return d

    @cached_property
    def objs(self):
        d = find_files(self.package.rootdir / "src", "*.c", ".o")
        if self.archdir:
            d.update(find_files(self.archdir / "src", "*.c", ".o", "asm"))
        return d

    @cached_property
    def includefiles(self):
        d = find_files(self.package.rootdir / "include", "*.h", ".h")
        if self.archdir:
            d.update(find_files(self.archdir / "include", "*.h", ".h"))
        return d

    @cached_property
    def includedeps(self):
        deps = set()
        for f in self.includefiles.values():
            deps.update(get_include_deps(self.includedirs, f))
        for f in self.objs.values():
            deps.update(get_include_deps(self.includedirs, f))
        for f in self.bins.values():
            deps.update(get_include_deps(self.includedirs, f))
        return [f"<{h}>" for h in deps]

    def write_flags(self, rootdir, ninja, flags):
        if flags.cflags:
            ninja.variable('cflags', ['$cflags'] + flags.cflags)
        if flags.ldflags:
            ninja.variable('ldflags', ['$ldflags'] + flags.ldflags)
        if flags.linker_script:
            script = (self.package.rootdir / flags.linker_script).relative_to(rootdir, walk_up=True).as_posix()
            ninja.variable('linker-script-flags', f"-Wl,--script={script}")
            ninja.variable('linker-script', script)

    def write_build_flags(self, rootdir, ninja):
        self.write_flags(rootdir, ninja, self.build_flags)

    def write_build_export(self, rootdir, ninja):
        self.write_flags(rootdir, ninja, self.export_flags)

    def write_build_objs(self, rootdir, ninja, objs):
        result = []
        keys = list(sorted(objs))
        for key in keys:
            dst = "$basedir/" + key.with_suffix(".o").as_posix()
            src = objs[key].relative_to(rootdir, walk_up=True).as_posix()
            ninja.build([dst], "cc", [src])
            result.append(dst)
        return result

    def write_build_lib(self, rootdir, lib_ninja):
        with NinjaWriter(rootdir / lib_ninja) as ninja:
            self.write_build_flags(rootdir, ninja)
            ninja.variable('basedir', lib_ninja.parent.as_posix())
            objs = self.write_build_objs(rootdir, ninja, self.objs)
            libname = f"lib/lib{self.id.name}.a"
            ninja.build([libname], "ar", objs)
            return libname

    def write_build_bin(self, rootdir, lib_ninja):
        with NinjaWriter(rootdir / lib_ninja) as ninja:
            self.write_build_flags(rootdir, ninja)
            ninja.variable('basedir', lib_ninja.parent.as_posix())
            objs = self.write_build_objs(rootdir, ninja, self.bins)
            ninja.build(['lib/bin.a'], "ar", objs)
            for dst in self.bins:
                src = "$basedir/" + dst.with_suffix(".o").as_posix()
                bin = ('bin' / dst).as_posix()
                ninja.build([bin], "ld", [src], ['libs', '$linker-script'])
