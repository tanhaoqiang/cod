# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from collections import defaultdict

from pydantic import BaseModel

def normalize_flags(flags):
    if isinstance(flags, str):
        return [flags]
    elif flags:
        return flags
    else:
        return []

class BuildFlags(BaseModel):
    cflags: str | list[str] | None = None
    ldflags: str | list[str] | None = None

    def normalize(self):
        return BuildFlags(
            cflags = normalize_flags(self.cflags),
            ldflags = normalize_flags(self.ldflags))

    def __add__(self, other):
        a = self.normalize()
        b = other.normalize()
        return BuildFlags(
            cflags = a.cflags + b.cflags,
            ldflags = a.ldflags + b.ldflags)

class Package(BaseModel):
    name: str
    version: str
    epoch: int = 0
    release: str = '0'
    arch: list[str] | None = None

class Profile(BaseModel):
    build: dict[str, BuildFlags] | BuildFlags = BuildFlags()

class Manifest(BaseModel):
    package: Package
    export: dict[str, BuildFlags] | BuildFlags = BuildFlags()
    build: dict[str, BuildFlags] | BuildFlags = BuildFlags()
    profile: dict[str, Profile] = {}
