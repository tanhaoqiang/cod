# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from io import StringIO

from ninja.ninja_syntax import Writer

class NinjaWriter:

    def __init__(self, path):
        self.path = path
        self._writer = Writer(StringIO())

    def __enter__(self):
        return self._writer

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            return

        new = self._writer.output.getvalue()

        try:
            f = self.path.open("r")
        except FileNotFoundError:
            pass
        else:
            with f:
                old = f.read()
            if old == new:
                return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            f.write(new)
