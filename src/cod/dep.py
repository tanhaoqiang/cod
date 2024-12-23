# Copyright (c) 2024 tanhaoqiang
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

def parse_dep(s):
    for line in iter_lines(s):
        parts = shlex.split(line, comments=True)
        if not parts:
            continue
        for name in parts[1:]:
            yield name.replace('$$', '$')

def get_include_deps(workdir, includedir, files):
    if not files:
        return []

    deps = []
    for name in files:
        dep = check_output(
            [sys.executable, "-mziglang", "cc",
             "-I", includedir.relative_to(workdir, walk_up=True),
             "-MM", "-MG", name],
            cwd = workdir).decode()
        deps.extend(parse_dep(dep))
    return [name for name in deps if not (workdir / name).exists()]

def get_symbol_deps(workdir, obj):
    script = Path(__file__).parent / "always-fail.ld"
    proc = run(
        [sys.executable, "-mziglang", "cc", f"-Wl,--script={script}", obj],
        stderr=PIPE, text=True, cwd=workdir)
    return re.findall(r': error: undefined symbol: (\S+)$', proc.stderr, re.MULTILINE)
