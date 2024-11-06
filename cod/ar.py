# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from struct import unpack

def parse_armap(f):
    assert f.read(8) == b'!<arch>\n', "BAD MAGIC"
    name = f.read(16)
    if not name:
        return []
    name = name.rstrip()
    date = int(f.read(12).rstrip())
    uid = int(f.read(6).rstrip())
    gid = int(f.read(6).rstrip())
    mode = int(f.read(8).rstrip(), 8)
    size = int(f.read(10))
    assert f.read(2) == b"`\n"
    assert name == b'/'
    assert mode == 0
    content = f.read(size)
    n, = unpack("!I", content[0:4])
    assert content[-1] == 0
    names = content[4+n*4:].rstrip(b'\x00').split(b'\x00')
    assert len(names) == n
    return [name.decode() for name in names]
