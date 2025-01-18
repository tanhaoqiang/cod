# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import json

from .repo import Repo
from .compat import cached_property

class LocalRepo(Repo):

    def __init__(self, config_dir, cache_dir, config):
        self.rootdir = config_dir/config['path']

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
        path = self.packages[pkgid]
        with path.open() as f:
            return json.load(f)

    def get_path(self, pkgid):
        return self.packages[pkgid].parent.parent
