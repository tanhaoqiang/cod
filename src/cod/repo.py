# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from .compat import entry_points

repo_plugins = entry_points(group=f'{__package__}.repos')

class Repo:

    def __new__(self, cache_dir, config):
        return object.__new__(repo_plugins[config.pop('type')].load())

    def __iter__(self):
        raise NotImplementedError

    def fetch(self, pkgid):
        raise NotImplementedError

    def get_info(self, pkgid):
        raise NotImplementedError

    def get_path(self, pkgid):
        raise NotImplementedError
