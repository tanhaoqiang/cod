# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
import sys
from configparser import ConfigParser
from subprocess import check_call, check_output
from ninja.ninja_syntax import Writer as NinjaWriter
import shlex
from .pkgdb import PackageDatabase

def iter_lines(s):
    full = ''

    for line in s.splitlines():
        full += line
        if full.endswith('\\'):
            full += "\n"
        else:
            yield full
            full = ''

    if full:
        yield full

def parse_dep(s):
    for line in iter_lines(s):
        parts = shlex.split(line, comments=True)
        if not parts:
            continue
        for name in parts[1:]:
            yield name.replace('$$', '$')

class Config:

    def __init__(self, rootdir=None):
        self.rootdir = Path.cwd()
        self.srcdir = self.rootdir / 'src'
        self.includedir = self.rootdir / 'include'
        self.builddir = self.rootdir / 'build'

        parser = ConfigParser()
        with (self.rootdir / "cod.ini").open() as f:
            parser.read_file(f)

        self.name = parser['cod']['name']
        self.version = parser['cod']['version']
        self.kind = parser['cod']['kind']

        if parser.has_section('repo'):
            self.db = PackageDatabase()
            self.db.add_repo(
                parser['repo']['name'],
                self.rootdir / parser['repo']['path'])

    def get_cfiles(self):
        return [f.relative_to(self.srcdir) for f in self.srcdir.rglob("*.c")]

    def get_hfiles(self):
        return [f.relative_to(self.includedir) for f in self.includedir.rglob("*.h")]

    def generate_lib_ninja(self):
        cfiles = self.get_cfiles()
        hfiles = self.get_hfiles()

        self.builddir.mkdir(exist_ok=True)

        with (self.builddir / "build.ninja").open("w") as f:
            ninja = NinjaWriter(f)
            includedir = self.includedir.relative_to(self.builddir, walk_up=True)

            ninja.variable('python', [sys.executable])
            ninja.variable('zig', ["$python", "-mziglang"])
            ninja.variable('pkg', ["$python", "-mcod._pkg"])
            ninja.variable('cc', ["$zig", "cc"])
            ninja.variable('ar', ["$zig", "ar"])
            ninja.variable('cflags', ["-I", includedir.as_posix()])

            ninja.rule('cc', ["$cc", "$cflags", "-c", "$in", "-o", "$out"])
            ninja.rule('ar', ["$ar", "crs", "$out", "$in"])
            ninja.rule('pkg', ["$pkg", self.name, self.version, includedir.as_posix(), "$out", "$in"])

            for path in cfiles:
                obj = path.with_suffix(".o")
                src = (self.srcdir/path).relative_to(self.builddir, walk_up=True)
                ninja.build([obj.as_posix()], "cc", [src.as_posix()])
            ninja.build([f"lib{self.name}.a"], "ar", [path.with_suffix(".o").as_posix() for path in cfiles])

            ninja.build(
                [f"{self.name}.cod"],
                "pkg",
                [f"lib{self.name}.a"] +
                [ (self.includedir / path).relative_to(self.builddir, walk_up=True).as_posix()
                  for path in hfiles ])

    def get_missing_headers(self):
        cfiles = self.get_cfiles()
        dep = check_output(
            [sys.executable, "-mziglang", "cc",
             "-I", self.includedir.relative_to(self.srcdir, walk_up=True),
             "-MM", "-MG"] + cfiles,
            cwd=self.srcdir).decode()
        return [
            name
            for name in parse_dep(dep)
            if not (self.srcdir / name).exists()]

    def build(self):
        if self.kind == 'lib':
            self.generate_lib_ninja()
            check_call([sys.executable, "-mninja"], cwd=self.builddir)
        elif self.kind == 'exe':
            files = self.get_missing_headers()
            self.db.solve_files(files)
        else:
            assert False

def main():
    c = Config()
    c.build()
