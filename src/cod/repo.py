# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

repo_plugins = entry_points(group=f'{__package__}.repos')

class Repo:

    def __new__(self, config_dir, cache_dir, config):
        return object.__new__(repo_plugins[config.pop('type')].load())

    def __iter__(self):
        raise NotImplementedError

    def fetch(self, pkgid):
        raise NotImplementedError

    def get_info(self, pkgid):
        raise NotImplementedError

    def get_path(self, pkgid):
        raise NotImplementedError
