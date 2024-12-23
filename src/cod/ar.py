# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from pathlib import Path
from subprocess import call

def main(archive, *files):
    try:
        Path(archive).unlink()
    except FileNotFoundError:
        pass
    exit(call((sys.executable, "-mziglang", "ar", "qcs", "--thin", archive) + files))

if __name__ == '__main__':
    main(*sys.argv[1:])
