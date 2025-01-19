# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

def update_file(path, new):
    try:
        f = path.open("r")
    except FileNotFoundError:
        pass
    else:
        with f:
            old = f.read()
        if old == new:
            return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(new)
