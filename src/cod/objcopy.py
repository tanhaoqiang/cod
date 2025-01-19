# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from os import SEEK_SET

from .elf import copy_content, sizeof, get_elf_class, PT_LOAD

def get_phdrs(f):
    f.seek(0, SEEK_SET)
    Elf = get_elf_class(f)

    f.seek(0, SEEK_SET)
    ehdr = Elf.Ehdr.from_buffer_copy(f.read(sizeof(Elf.Ehdr)))

    f.seek(ehdr.e_phoff, SEEK_SET)
    results = []
    for i in range(ehdr.e_phnum):
        data = f.read(ehdr.e_phentsize)
        phdr = Elf.Phdr.from_buffer_copy(data[:sizeof(Elf.Phdr)])
        results.append(phdr)
    return results

def main(outfile, infile):
    with open(infile, "rb") as inf:
        phdrs = get_phdrs(inf)
        with open(outfile, "wb") as outf:
            for phdr in phdrs:
                if phdr.p_type != PT_LOAD:
                    continue

                inf.seek(phdr.p_offset, SEEK_SET)
                outf.seek(phdr.p_paddr, SEEK_SET)
                copy_content(inf, outf, phdr.p_filesz)
                outf.seek(phdr.p_paddr + phdr.p_memsz, SEEK_SET)

if __name__ == '__main__':
    main(*sys.argv[1:])
