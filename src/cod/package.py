# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass
from functools import cached_property
import tomllib

from .dep import get_include_deps

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

def find_files(path, pattern):
    return [f.relative_to(path) for f in path.rglob(pattern)]

class Package:

    def __init__(self, rootdir):
        self.rootdir = rootdir
        self.includedir = rootdir / "include"
        self.srcdir = rootdir / "src"
        self.bindir = rootdir / "bin"

        with (self.rootdir / "cod.toml").open("rb") as f:
            toml = tomllib.load(f)
        self._toml = toml
        package = toml['package']
        evr = EVR(
            package.get('epoch', 0),
            package['version'],
            package.get('release', '0'))
        self.id = PackageId(package['name'], str(evr), package.get('arch', 'noarch'))

    @cached_property
    def includefiles(self):
        return find_files(self.includedir, "*.h")

    @cached_property
    def srcfiles(self):
        return find_files(self.srcdir, "*.c")

    @cached_property
    def binfiles(self):
        return find_files(self.bindir, "*.c")

    @cached_property
    def includedeps(self):
        deps = set()
        deps.update(get_include_deps(self.includedir, self.includedir, self.includefiles))
        deps.update(get_include_deps(self.srcdir, self.includedir, self.srcfiles))
        deps.update(get_include_deps(self.bindir, self.includedir, self.binfiles))
        return [f"<{h}>" for h in deps]
