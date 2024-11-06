# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
import sys
import json
from .ar import parse_armap

def main():
    name, version, include, out, archive, *headers = sys.argv[1:]

    with open(archive, "rb") as f:
        symbols = parse_armap(f)

    includedir = Path(include)
    filelist = [Path(h).relative_to(includedir).as_posix() for h in headers]

    with open(out, "w") as f:
        json.dump(
            {"name": name,
             "version": version,
             "provides": [f"({s})" for s in symbols],
             "filelist": filelist},
            f)

if __name__ == '__main__':
    main()
