# Copyright (c) 2024 tanhaoqiang
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
    repo: dict[str, dict] = {}
    profile: dict[str, dict] = {}
