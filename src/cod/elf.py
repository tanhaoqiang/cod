# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from ctypes import (
    Structure,
    sizeof,
    c_ubyte,
    c_char,
    c_uint16,
    c_uint32,
    c_uint64,
    c_int32,
    c_int64,
)

Elf32_Half    = c_uint16
Elf64_Half    = c_uint16
Elf32_Word    = c_uint32
Elf64_Word    = c_uint32
Elf32_Sword   = c_int32
Elf32_Xword   = c_uint64
Elf64_Xword   = c_uint64
Elf64_Sxword  = c_int64
Elf32_Addr    = c_uint32
Elf64_Addr    = c_uint64
Elf32_Off     = c_uint32
Elf64_Off     = c_uint64
Elf32_Section = c_uint16
Elf64_Section = c_uint16

EI_NIDENT = 16
ELFMAG = b"\x7FELF"
SELFMAG = 4

EI_CLASS = 4
ELFCLASS32   = 1
ELFCLASS64   = 2

EI_DATA = 5
ELFDATA2LSB = 1

EI_VERSION = 6

EI_OSABI = 7
ELFOSABI_SYSV = 0

ET_REL = 1

EM_I386   = 3
EM_AMD64 = 62

SHT_NULL     = 0
SHT_PROGBITS = 1
SHT_SYMTAB   = 2
SHT_STRTAB   = 3
SHT_RELA     = 4
SHT_NOBITS   = 8
SHT_REL      = 9
SHT_LOOS     = 0x60000000
SHT_LLVM_ADDRSIG = SHT_LOOS + 0xfff4c03

PT_LOAD = 1

R_I386_32   = 1
R_I386_PC32 = 2
R_I386_16   = 20
R_I386_PC16 = 21
R_I386_8    = 22
R_I386_PC8  = 23

R_AMD64_PC32 = 2
R_AMD64_32   = 10
R_AMD64_16   = 12
R_AMD64_PC16 = 13
R_AMD64_8    = 14
R_AMD64_PC8  = 15

class Elf32_Ehdr(Structure):
    _fields_ = [
        ("e_ident",     c_ubyte * EI_NIDENT),
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
        ("e_ident",     c_ubyte * EI_NIDENT),
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

class Elf32_Shdr(Structure):
    _fields_ = [
        ("sh_name",      Elf32_Word),
        ("sh_type",      Elf32_Word),
        ("sh_flags",     Elf32_Word),
        ("sh_addr",      Elf32_Addr),
        ("sh_offset",    Elf32_Off),
        ("sh_size",      Elf32_Word),
        ("sh_link",      Elf32_Word),
        ("sh_info",      Elf32_Word),
        ("sh_addralign", Elf32_Word),
        ("sh_entsize",   Elf32_Word),
    ]

class Elf64_Shdr(Structure):
    _fields_ = [
        ("sh_name",      Elf64_Word),
        ("sh_type",      Elf64_Word),
        ("sh_flags",     Elf64_Xword),
        ("sh_addr",      Elf64_Addr),
        ("sh_offset",    Elf64_Off),
        ("sh_size",      Elf64_Xword),
        ("sh_link",      Elf64_Word),
        ("sh_info",      Elf64_Word),
        ("sh_addralign", Elf64_Xword),
        ("sh_entsize",   Elf64_Xword),
    ]

class Elf32_Sym(Structure):
    _fields_ = [
        ("st_name",  Elf32_Word),
        ("st_value", Elf32_Addr),
        ("st_size",  Elf32_Word),
        ("st_info",  c_ubyte),
        ("st_other", c_ubyte),
        ("st_shndx", Elf32_Section),
    ]

class Elf64_Sym(Structure):
    _fields_ = [
        ("st_name",  Elf64_Word),
        ("st_info",  c_ubyte),
        ("st_other", c_ubyte),
        ("st_shndx", Elf64_Section),
        ("st_value", Elf64_Addr),
        ("st_size",  Elf64_Xword),
    ]

class Elf32_Rel(Structure):
    _fields_ = [
        ("r_offset", Elf32_Addr),
        ("r_info",   Elf32_Word),
    ]

class Elf64_Rel(Structure):
    _fields_ = [
        ("r_offset", Elf64_Addr),
        ("r_info",   Elf64_Xword),
    ]

class Elf32_Rela(Structure):
    _fields_ = [
        ("r_offset", Elf32_Addr),
        ("r_info",   Elf32_Word),
        ("r_addend", Elf32_Sword),
    ]

class Elf64_Rela(Structure):
    _fields_ = [
        ("r_offset", Elf64_Addr),
        ("r_info",   Elf64_Xword),
        ("r_addend", Elf64_Sxword),
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
    Shdr = Elf32_Shdr
    Sym  = Elf32_Sym
    Rel  = Elf32_Rel
    Rela = Elf32_Rela
    Phdr = Elf32_Phdr

class Elf64:
    Ehdr = Elf64_Ehdr
    Shdr = Elf64_Shdr
    Sym  = Elf64_Sym
    Rel  = Elf64_Rel
    Rela = Elf64_Rela
    Phdr = Elf64_Phdr

def get_elf_class(f):
    ident = f.read(EI_NIDENT)
    assert ident[:SELFMAG] == ELFMAG, "bad magic"
    return {ELFCLASS32: Elf32, ELFCLASS64: Elf64}[ident[EI_CLASS]]

BUFSZ = 4096

def copy_content(inf, outf, length):
    while length > BUFSZ:
        data = inf.read(BUFSZ)
        outf.write(data)
        length -= BUFSZ

    if length:
        data = inf.read(length)
        outf.write(data)
