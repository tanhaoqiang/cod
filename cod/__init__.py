# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
import sys
from configparser import ConfigParser
from subprocess import run, check_call, check_output, PIPE
import re
import shlex
import argparse
from ninja.ninja_syntax import Writer as NinjaWriter
from .pkgdb import PackageDatabase
from .ar import parse_armap

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
            repos = {parser['repo']['name']: self.rootdir / parser['repo']['path']}
        else:
            repos = {}

        self.db = PackageDatabase(self.builddir, repos)

    def get_cfiles(self, srcdir=None):
        srcdir = srcdir or self.srcdir
        return [f.relative_to(srcdir) for f in srcdir.rglob("*.c")]

    def get_hfiles(self):
        return [f.relative_to(self.includedir) for f in self.includedir.rglob("*.h")]

    def generate_ninja(self, packages):
        cfiles = self.get_cfiles()
        self.builddir.mkdir(exist_ok=True)

        with (self.builddir / "build.ninja").open("w") as f:
            ninja = NinjaWriter(f)
            includedir = self.includedir.relative_to(self.builddir, walk_up=True)
            includedirs = [includedir]

            (self.builddir / self.name).mkdir(exist_ok=True)

            for package in packages:
                includedirs.append((package.parent.parent / "include").relative_to(self.builddir, walk_up=True))
                (self.builddir / package.stem).mkdir(exist_ok=True)

            ninja.variable('python', [sys.executable])
            ninja.variable('zig', ["$python", "-mziglang"])
            ninja.variable('cc', ["$zig", "cc"])
            ninja.variable('ar', ["$zig", "ar"])
            ninja.variable('cflags', [a for d in includedirs for a in ["-I", d.as_posix()]])

            ninja.rule('cc', ["$cc", "$cflags", "-c", "$in", "-o", "$out"])
            ninja.rule('ar', ["$ar", "crs", "$out", "$in"])

            for path in cfiles:
                obj = path.with_suffix(".o")
                src = (self.srcdir/path).relative_to(self.builddir, walk_up=True)
                ninja.build([f"{self.name}/{obj.as_posix()}"], "cc", [src.as_posix()])
            ninja.build([f"lib{self.name}.a"], "ar", [f"{self.name}/{path.with_suffix('.o').as_posix()}" for path in cfiles])

            for package in packages:
                srcdir = package.parent.parent / "src"
                pcfiles = self.get_cfiles(srcdir)
                for path in pcfiles:
                    obj = path.with_suffix(".o")
                    src = (srcdir/path).relative_to(self.builddir, walk_up=True)
                    ninja.build([f"{package.stem}/{obj.as_posix()}"], "cc", [src.as_posix()])
                ninja.build([f"lib{package.stem}.a"], "ar", [f"{package.stem}/{path.with_suffix('.o').as_posix()}" for path in pcfiles])

            if self.kind == 'lib':
                hfiles = self.get_hfiles()
                ninja.variable('pkg', ["$python", "-mcod._pkg"])
                ninja.rule('pkg', ["$pkg", self.name, self.version, includedir.as_posix(), "$out", "$in"])
                ninja.build(
                    [f"{self.name}.cod"],
                    "pkg",
                    [f"lib{self.name}.a"] +
                    [ (self.includedir / path).relative_to(self.builddir, walk_up=True).as_posix()
                      for path in hfiles ])
            elif self.kind == 'exe':
                ninja.rule('ld', ["$cc", "$in", "-o", "$out"])
                ninja.build([f"{self.name}.exe"], "ld",
                            [f"lib{self.name}.a"] + [
                                f"lib{package.stem}.a"
                                for package in packages ])
            else:
                assert False

    def get_missing_headers(self):
        cfiles = self.get_cfiles()
        if not cfiles:
            return []

        dep = check_output(
            [sys.executable, "-mziglang", "cc",
             "-I", self.includedir.relative_to(self.srcdir, walk_up=True),
             "-MM", "-MG"] + cfiles,
            cwd=self.srcdir).decode()
        return [
            name
            for name in parse_dep(dep)
            if not (self.srcdir / name).exists()]

    def get_missing_symbols(self, packages):
        archives = [f"lib{self.name}.a"] + [f"lib{package.stem}.a" for package in packages ]
        undefined = set()
        defined = set()

        for name in archives:
            proc = run([sys.executable, "-mziglang", "cc", "-Wl,--no-undefined", f"{name}.a"], stderr=PIPE, text=True, cwd=self.builddir)
            if proc.returncode != 0:
                symbols = re.findall(r'^ld.lld: error: undefined symbol: (\S+)', proc.stderr, re.MULTILINE)
                undefined.update(symbols)
            with (self.builddir/name).open("rb") as f:
                defined.update(parse_armap(f))

        return list(undefined - defined)


    def build(self):
        files = self.get_missing_headers()
        self.db.install_from_filelist(files)
        packages = self.db.get_installed()
        self.generate_ninja(packages)

        if self.kind == 'lib':
            check_call([sys.executable, "-mninja"], cwd=self.builddir)
        elif self.kind == 'exe':
            archives = [f"lib{self.name}.a"] + [f"lib{package.stem}.a" for package in packages ]
            check_call([sys.executable, "-mninja"] + archives, cwd=self.builddir)
            symbols = self.get_missing_symbols(packages)
            if symbols:
                self.db.install_from_symbols(symbols)
                self.generate_ninja(self.db.get_installed())
            check_call([sys.executable, "-mninja", f"{self.name}.exe"], cwd=self.builddir)
        else:
            assert False


    def install(self, packages):
        self.db.install_packages(packages)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    parser_build = subparsers.add_parser('build')
    parser_install = subparsers.add_parser('install')
    parser_install.add_argument('package', nargs='+')
    args = parser.parse_args()

    c = Config()
    if args.command == 'build':
        c.build()
    elif args.command == 'install':
        c.install(args.package)
    else:
        parser.print_help()
