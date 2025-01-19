# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from .repo import Repo
from .manifest import ProjectManifest, write_compiler_variables
from .compat import tomllib, cached_property

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
        return {
            name: Repo(self.rootdir, self.repodir(name), config)
            for name, config in self.manifest.repo.items()}

    def write_build_variables(self, ninja):
        write_compiler_variables(ninja, self.manifest.build)
