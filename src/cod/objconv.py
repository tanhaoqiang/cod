# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from os import SEEK_SET
from io import BytesIO

from .elf import (
    copy_content, sizeof, get_elf_class, Elf32, Elf64,
    EI_CLASS, ELFCLASS64,
    EI_DATA, ELFDATA2LSB,
    EI_VERSION,
    EI_OSABI, ELFOSABI_SYSV,
    ET_REL, EM_I386, EM_AMD64,
    SHT_NULL, SHT_PROGBITS, SHT_SYMTAB, SHT_STRTAB, SHT_RELA, SHT_NOBITS, SHT_REL, SHT_LLVM_ADDRSIG,
    R_I386_32, R_I386_PC32, R_I386_16, R_I386_PC16, R_I386_8, R_I386_PC8,
    R_AMD64_32, R_AMD64_PC32, R_AMD64_16, R_AMD64_PC16, R_AMD64_8, R_AMD64_PC8,
)

def get_ehdr(f):
    f.seek(0, SEEK_SET)
    Elf = get_elf_class(f)
    assert Elf is Elf32, "Class must be ELF32"

    ehsize = sizeof(Elf.Ehdr)
    shentsize = sizeof(Elf.Shdr)

    f.seek(0, SEEK_SET)
    ehdr = Elf.Ehdr.from_buffer_copy(f.read(ehsize))

    assert ehdr.e_version == 1, "Version must be 1"
    assert ehdr.e_ehsize == ehsize, f"Size of ELF header other than {ehsize} not supported"
    assert ehdr.e_shentsize == shentsize, f"Size of section header other than {shentsize} not supported"

    assert ehdr.e_type == ET_REL, "Type other than REL (Relocatable file) not supported"
    assert ehdr.e_machine == EM_I386, "Machine other than Intel 80386 not supported"

    ident = ehdr.e_ident
    assert ident[EI_VERSION] == 1, "Version must be 1"
    assert ident[EI_DATA] == ELFDATA2LSB, "Data encoding must be 2's complement, little endian"
    assert ident[EI_OSABI] == ELFOSABI_SYSV, "OS/ABI must be UNIX - System V"
    return ehdr

def get_shdrs(f, ehdr):
    f.seek(ehdr.e_shoff, SEEK_SET)
    results = []
    for i in range(ehdr.e_shnum):
        data = f.read(ehdr.e_shentsize)
        shdr = Elf32.Shdr.from_buffer_copy(data[:sizeof(Elf32.Shdr)])
        results.append(shdr)
    return results

def main(outfile, infile):
    buf = BytesIO()
    with open(infile, "rb") as f:
        ehdr32 = get_ehdr(f)
        shdrs32 = get_shdrs(f, ehdr32)
        shdrs64 = []

        ehdr64 = Elf64.Ehdr()
        ehdr64.e_ident = ehdr32.e_ident
        ehdr64.e_ident[EI_CLASS] = ELFCLASS64

        ehdr64.e_type = ehdr32.e_type
        ehdr64.e_machine = EM_AMD64
        ehdr64.e_version = ehdr32.e_version
        ehdr64.e_entry = 0
        ehdr64.e_phoff = 0
        ehdr64.e_flags = ehdr32.e_flags
        ehdr64.e_ehsize = sizeof(Elf64.Ehdr)
        ehdr64.e_phentsize = 0
        ehdr64.e_phnum = 0
        ehdr64.e_shentsize = sizeof(Elf64.Shdr)
        ehdr64.e_shnum = ehdr32.e_shnum
        ehdr64.e_shstrndx = ehdr32.e_shstrndx

        buf.seek(ehdr64.e_ehsize, SEEK_SET)

        for index, shdr32 in enumerate(shdrs32):
            shdr64 = Elf64.Shdr()
            shdrs64.append(shdr64)

            shdr64.sh_name = shdr32.sh_name
            shdr64.sh_type = shdr32.sh_type
            shdr64.sh_flags = shdr32.sh_flags
            shdr64.sh_addr = shdr32.sh_flags
            shdr64.sh_link = shdr32.sh_link
            shdr64.sh_info = shdr32.sh_info
            shdr64.sh_addralign = shdr32.sh_addralign
            shdr64.sh_size = shdr32.sh_size
            shdr64.sh_offset = buf.tell()
            shdr64.sh_entsize = shdr32.sh_entsize
            f.seek(shdr32.sh_offset, SEEK_SET)

            if (shdr32.sh_type in (SHT_NULL, SHT_PROGBITS, SHT_STRTAB, SHT_LLVM_ADDRSIG)) or (shdr32.sh_size == 0):
                copy_content(f, buf, shdr32.sh_size)
            elif shdr32.sh_type == SHT_NOBITS:
                pass
            elif shdr32.sh_type == SHT_SYMTAB:
                entsize = sizeof(Elf32.Sym)
                assert shdr32.sh_entsize == entsize, f"Size of Sym other than {entsize} not supported"
                shdr64.sh_entsize = sizeof(Elf64.Sym)

                for offset in range(0, shdr32.sh_size, shdr32.sh_entsize):
                    sym32 = Elf32.Sym.from_buffer_copy(f.read(entsize))
                    sym64 = Elf64.Sym()
                    sym64.st_name = sym32.st_name
                    sym64.st_info  = sym32.st_info
                    sym64.st_other = sym32.st_other
                    sym64.st_value = sym32.st_value
                    sym64.st_size = sym32.st_size
                    sym64.st_shndx = sym32.st_shndx
                    buf.write(bytes(sym64))

                shdr64.sh_size = buf.tell() - shdr64.sh_offset
            elif shdr32.sh_type == SHT_REL:
                entsize = sizeof(Elf32.Rel)
                assert shdr32.sh_entsize == entsize, f"Size of Rel other than {entsize} not supported"
                shdr64.sh_entsize = sizeof(Elf64.Rela)
                shdr64.sh_type = SHT_RELA

                assert index > shdr32.sh_info
                sh_offset = shdrs64[shdr32.sh_info].sh_offset
                relas64 = []

                for offset in range(0, shdr32.sh_size, shdr32.sh_entsize):
                    rel32 = Elf32.Rel.from_buffer_copy(f.read(entsize))
                    rela64 = Elf64.Rela()
                    rela64.r_offset = rel32.r_offset
                    type32 = rel32.r_info & 0xFF
                    sym = rel32.r_info >> 8

                    type64, nbytes, signed = {
                        R_I386_32: (R_AMD64_32, 4, False),
                        R_I386_PC32: (R_AMD64_PC32, 4, True),
                        R_I386_16: (R_AMD64_16, 2, False),
                        R_I386_PC16: (R_AMD64_PC16, 2, True),
                        R_I386_8: (R_AMD64_8, 1, False),
                        R_I386_PC8: (R_AMD64_PC8, 1, True),
                    }[type32]

                    addend_offset = rel32.r_offset + sh_offset
                    buf.seek(addend_offset, SEEK_SET)
                    addend = buf.read(nbytes)
                    buf.seek(addend_offset, SEEK_SET)
                    buf.write(b"\x00" * nbytes)

                    rela64.r_addend = int.from_bytes(addend, byteorder='little', signed=signed)
                    rela64.r_info = (sym << 32) | type64
                    relas64.append(rela64)

                buf.seek(shdr64.sh_offset, SEEK_SET)
                for rela64 in relas64:
                    buf.write(bytes(rela64))
                shdr64.sh_size = buf.tell() - shdr64.sh_offset

            else:
                assert False, f"Section type {shdr32.sh_type} not supported"

        ehdr64.e_shoff = buf.tell()
        for shdr64 in shdrs64:
            buf.write(bytes(shdr64))

        buf.seek(0, SEEK_SET)
        buf.write(bytes(ehdr64))

    with open(outfile, "wb") as f:
        f.write(buf.getvalue())

if __name__ == '__main__':
    main(*sys.argv[1:])
