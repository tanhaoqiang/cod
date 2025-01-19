# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from io import StringIO

from ninja.ninja_syntax import Writer

from .util import update_file

class NinjaWriter:

    def __init__(self, path):
        self.path = path
        self._writer = Writer(StringIO())

    def __enter__(self):
        return self._writer

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            return

        update_file(self.path, self._writer.output.getvalue())
