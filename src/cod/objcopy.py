# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from os import SEEK_SET
from ctypes import (
    Structure,
    sizeof,
    c_char,
    c_uint16,
    c_uint32,
    c_uint64,
)

Elf32_Half = c_uint16
Elf64_Half = c_uint16
Elf32_Word = c_uint32
Elf64_Word = c_uint32
Elf32_Addr = c_uint32
Elf64_Addr = c_uint64
Elf32_Off  = c_uint32
Elf64_Off  = c_uint64

EI_NIDENT = 16
ELFMAG = b"\x7FELF"
SELFMAG = 4

EI_CLASS = 4

ELFCLASSNONE = 0
ELFCLASS32   = 1
ELFCLASS64   = 2

PT_LOAD = 1

class Elf32_Ehdr(Structure):
    _fields_ = [
        ("e_ident",     c_char * EI_NIDENT),
        ("e_type",      Elf32_Half),
        ("e_machine",   Elf32_Half),
        ("e_version",   Elf32_Word),
        ("e_entry",     Elf32_Addr),
        ("e_phoff",     Elf32_Off),
        ("e_shoff",     Elf32_Off),
        ("e_flags",     Elf32_Word),
        ("e_ehsize",    Elf32_Half),
        ("e_phentsize", Elf32_Half),
        ("e_phnum",     Elf32_Half),
        ("e_shentsize", Elf32_Half),
        ("e_shnum",     Elf32_Half),
        ("e_shstrndx",  Elf32_Half),
    ]

class Elf64_Ehdr(Structure):
    _fields_ = [
        ("e_ident",     c_char * EI_NIDENT),
        ("e_type",      Elf64_Half),
        ("e_machine",   Elf64_Half),
        ("e_version",   Elf64_Word),
        ("e_entry",     Elf64_Addr),
        ("e_phoff",     Elf64_Off),
        ("e_shoff",     Elf64_Off),
        ("e_flags",     Elf64_Word),
        ("e_ehsize",    Elf64_Half),
        ("e_phentsize", Elf64_Half),
        ("e_phnum",     Elf64_Half),
        ("e_shentsize", Elf64_Half),
        ("e_shnum",     Elf64_Half),
        ("e_shstrndx",  Elf64_Half),
    ]

class Elf32_Phdr(Structure):
    _fields_ = [
        ("p_type",   Elf32_Word),
        ("p_offset", Elf32_Off),
        ("p_vaddr",  Elf32_Addr),
        ("p_paddr",  Elf32_Addr),
        ("p_filesz", Elf32_Word),
        ("p_memsz",  Elf32_Word),
        ("p_flags",  Elf32_Word),
        ("p_align",  Elf32_Word),
    ]

class Elf64_Phdr(Structure):
    _fields_ = [
        ("p_type",   Elf64_Word),
        ("p_offset", Elf64_Off),
        ("p_vaddr",  Elf64_Addr),
        ("p_paddr",  Elf64_Addr),
        ("p_filesz", Elf64_Word),
        ("p_memsz",  Elf64_Word),
        ("p_flags",  Elf64_Word),
        ("p_align",  Elf64_Word),
    ]

class Elf32:
    Ehdr = Elf32_Ehdr
    Phdr = Elf32_Phdr

class Elf64:
    Ehdr = Elf64_Ehdr
    Phdr = Elf64_Phdr

def get_phdrs(f):
    f.seek(0, SEEK_SET)
    ident = f.read(EI_NIDENT)
    assert ident[:SELFMAG] == ELFMAG, "bad magic"

    f.seek(0, SEEK_SET)
    Elf = {ELFCLASS32: Elf32, ELFCLASS64: Elf64}[ident[EI_CLASS]]
    ehdr = Elf.Ehdr.from_buffer_copy(f.read(sizeof(Elf.Ehdr)))

    f.seek(ehdr.e_phoff, SEEK_SET)
    results = []
    for i in range(ehdr.e_phnum):
        data = f.read(ehdr.e_phentsize)
        phdr = Elf.Phdr.from_buffer_copy(data[:sizeof(Elf.Phdr)])
        results.append(phdr)
    return results

BUFSZ = 4096

def copy_file_content(inf, outf, length):
    while length > BUFSZ:
        data = inf.read(BUFSZ)
        outf.write(data)
        length -= BUFSZ

    if length:
        data = inf.read(length)
        outf.write(data)

def main(outfile, infile):
    with open(infile, "rb") as inf:
        phdrs = get_phdrs(inf)
        with open(outfile, "wb") as outf:
            for phdr in phdrs:
                if phdr.p_type != PT_LOAD:
                    continue

                inf.seek(phdr.p_offset, SEEK_SET)
                outf.seek(phdr.p_paddr, SEEK_SET)
                copy_file_content(inf, outf, phdr.p_filesz)
                outf.seek(phdr.p_paddr + phdr.p_memsz, SEEK_SET)

if __name__ == '__main__':
    main(*sys.argv[1:])
