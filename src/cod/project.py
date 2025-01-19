# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
import json
from subprocess import check_call

from .repo import Repo
from .manifest import ProjectManifest, write_compiler_variables
from .package import PackageId, Package
from .compat import tomllib, cached_property

class ProjectLocalRepo:

    def __init__(self, rootdir):
        self.rootdir = rootdir

    @cached_property
    def packages(self):
        return {
            path.stem: path
            for path in self.rootdir.glob("*/.cod/*.cod")}

    def __iter__(self):
        return iter(self.packages)

    def fetch(self, pkgid):
        pass

    def get_info(self, pkgid):
        if pkgid not in self.packages:
            self.do_package(pkgid)
        path = self.packages[pkgid]
        with path.open() as f:
            return json.load(f)

    def get_path(self, pkgid):
        if pkgid not in self.packages:
            self.do_package(pkgid)
        return self.packages[pkgid].parent.parent

    def do_package(self, pkgid):
        avail = {path.parent for path in self.rootdir.glob("*/cod.toml")}
        found = {path.parent.parent for path in self.packages.values()}
        id = PackageId.from_str(pkgid)
        choices = []

        for path in avail-found:
            try:
                pkg = Package(path)
            except Exception:
                continue
            if pkg.name != id.name:
                continue
            if str(pkg.evr) != id.evr:
                continue
            if pkg.arch is None:
                if id.arch != 'noarch':
                    continue
            else:
                if id.arch not in pkg.arch:
                    continue
            choices.append(path)

        assert choices, f"package {pkgid} not found in project-local repo"
        assert len(choices) == 1, f"multiple package {pkgid} found in project-local repo"
        path = choices[0]
        check_call([sys.executable, f"-m{__package__}", "package"], cwd=path)
        self.packages[pkgid] = path / ".cod" / f"{pkgid}.cod"


def find_project_dir(pkg_dir):
    for p in pkg_dir.parents:
        if (p / "cod.toml").exists():
            return p
    assert False, "project directory not found"


class Project:

    def __init__(self, pkg_dir):
        self.rootdir = find_project_dir(pkg_dir)
        with (self.rootdir / "cod.toml").open("rb") as f:
            toml = tomllib.load(f)
        self.manifest = ProjectManifest.model_validate(toml)
        self.workdir = self.rootdir / ".cod"

    def repodir(self, name):
        return self.workdir / name

    @cached_property
    def repos(self):
        d = {
            name: Repo(self.repodir(name), config)
            for name, config in self.manifest.repo.items()}
        d["local"] = ProjectLocalRepo(self.rootdir)
        return d

    def write_build_variables(self, ninja):
        write_compiler_variables(ninja, self.manifest.build)
