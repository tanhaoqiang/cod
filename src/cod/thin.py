# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass
from struct import unpack
import os

@dataclass(frozen=True)
class Header:
    name: bytes
    date: bytes
    uid: bytes
    gid: bytes
    mode: bytes
    size: int

    @classmethod
    def parse(self, f):
        name = f.read(16).rstrip()
        date = f.read(12).rstrip()
        uid = f.read(6).rstrip()
        gid = f.read(6).rstrip()
        mode = f.read(8).rstrip()
        size = int(f.read(10))
        assert f.read(2) == b"`\n"
        return self(name, date, uid, gid, mode, size)

def parse_symbols(f):
    header = Header.parse(f)
    assert header.name == b'/'
    content = f.read(header.size)
    n, = unpack("!I", content[0:4])
    assert content[-1] == 0
    offsets = [unpack("!I", content[4+i*4:8+i*4])[0] for i in range(n)]
    names = content[4+n*4:].rstrip(b'\x00')
    if names:
        names = names.split(b'\x00')
    else:
        names = []
    assert len(names) == n
    return [(name.decode(), offset) for name, offset in zip(names, offsets)]

def parse_filenames(f):
    header = Header.parse(f)
    assert header.name == b'//'
    content = f.read(header.size)
    return content

def parse_armap(path):
    with path.open("rb") as f:
        assert f.read(8) == b'!<thin>\n', "BAD MAGIC"
        symbols = parse_symbols(f)
        filenames = parse_filenames(f)
        names = {}

        for offset in set(o for _, o in symbols):
            f.seek(offset)
            header = Header.parse(f)
            assert header.name.startswith(b'/')
            start = int(header.name[1:])
            end = filenames.find(b'/\n', start)
            assert end >= 0
            names[offset] = path.parent / filenames[start:end].decode()

    return [(name, names[offset]) for name, offset in symbols]
