# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from pydantic import BaseModel

class Package(BaseModel):
    name: str
    version: str
    epoch: int = 0
    release: str = '0'
    arch: list[str] | None = None

class Manifest(BaseModel):
    package: Package
    profile: dict[str, dict] = {}
