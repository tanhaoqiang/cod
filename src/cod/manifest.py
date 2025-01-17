# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from typing import List, Dict, Union, Optional

from pydantic import BaseModel, Field

def normalize_flags(flags):
    if isinstance(flags, str):
        return [flags]
    elif flags:
        return flags
    else:
        return []

class BuildFlags(BaseModel):
    class Config:
        populate_by_name = True

    cflags: Optional[Union[str, List[str]]] = None
    sflags: Optional[Union[str, List[str]]] = None
    ldflags: Optional[Union[str, List[str]]] = None
    linker_script: Optional[str] = Field(alias="linker-script", default=None)
    format: Optional[str] = None

    def normalize(self):
        return BuildFlags(
            cflags = normalize_flags(self.cflags),
            sflags = normalize_flags(self.sflags),
            ldflags = normalize_flags(self.ldflags),
            format = self.format,
            linker_script = self.linker_script)

    def __add__(self, other):
        a = self.normalize()
        b = other.normalize()
        return BuildFlags(
            cflags = a.cflags + b.cflags,
            sflags = a.sflags + b.sflags,
            ldflags = a.ldflags + b.ldflags,
            format = other.format or self.format,
            linker_script = other.linker_script or self.linker_script)

class Package(BaseModel):
    name: str
    version: str
    epoch: int = 0
    release: str = '0'
    arch: Optional[Union[str, List[str]]] = None

class Profile(BaseModel):
    build: Union[Dict[str, BuildFlags], BuildFlags] = BuildFlags()

class PackageManifest(BaseModel):
    package: Package
    export: Union[Dict[str, BuildFlags], BuildFlags] = BuildFlags()
    build: Union[Dict[str, BuildFlags], BuildFlags] = BuildFlags()
    profile: Dict[str, Profile] = {}

class Project(BaseModel):
    pass

class ProjectManifest(BaseModel):
    project: Project
    build: Union[Dict[str, BuildFlags], BuildFlags] = BuildFlags()
    repo: Dict[str, dict] = {}

def write_compiler_variables(ninja, flags, suffix=''):
    if isinstance(flags, dict):
        for k, v in flags.items():
            if k == 'noarch':
                write_compiler_variables(ninja, v)
            else:
                write_compiler_variables(ninja, v, f"-{k}")
        return

    flags = flags.normalize()
    if flags.cflags:
        ninja.variable(f'cflags{suffix}', [f'$cflags{suffix}'] + flags.cflags)
    if flags.sflags:
        ninja.variable(f'sflags{suffix}', [f'$sflags{suffix}'] + flags.sflags)
