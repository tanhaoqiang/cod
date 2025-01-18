# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys

if sys.version_info < (3, 8):
    from backports.cached_property import cached_property
else:
    from functools import cached_property

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

if sys.version_info < (3, 12):
    from posixpath import relpath

    def relative_to(self, other):
        return relpath(self.as_posix(), other.as_posix())
else:
    def relative_to(self, other):
        return self.relative_to(other, walk_up=True).as_posix()
