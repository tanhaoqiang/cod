# Copyright (c) 2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Dict

from pydantic import BaseModel

class Project(BaseModel):
    pass

class Manifest(BaseModel):
    project: Project
    repo: Dict[str, dict] = {}
