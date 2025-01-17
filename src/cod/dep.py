# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
import shlex
from subprocess import check_output, run, PIPE
from pathlib import Path
import re

def iter_lines(s):
    full = ''

    for line in s.splitlines():
        full += line
        if full.endswith('\\'):
            full = full[:-1] + "\n"
        else:
            yield full
            full = ''

    if full:
        yield full

def get_include_deps(includedirs, f, arch):
    argv = [sys.executable, "-mziglang", "clang", f"--target={arch}-unknown-unknown", "-nostdinc", "-MM", "-MG"]
    argv.extend(f"-I{i}" for i in includedirs)
    s = check_output(argv + [f.name], cwd = f.parent).decode()

    for line in iter_lines(s):
        parts = shlex.split(line, comments=True)
        if not parts:
            continue
        for name in parts[1:]:
            name = name.replace('$$', '$')
            if not (f.parent / name).exists():
                yield name

def get_symbol_deps(workdir, target, obj):
    script = Path(__file__).parent / "always-fail.ld"
    proc = run(
        [sys.executable, "-mziglang", "cc"] + target + [f"-Wl,--script={script}", str(obj)],
        stderr=PIPE, text=True, cwd=workdir)
    return re.findall(r': error: undefined symbol: (\S+)$', proc.stderr, re.MULTILINE)
