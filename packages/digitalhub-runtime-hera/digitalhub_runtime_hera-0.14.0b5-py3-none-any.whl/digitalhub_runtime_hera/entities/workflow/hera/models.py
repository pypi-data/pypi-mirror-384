# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SourceLang(Enum):
    """
    Source code language.
    """

    PYTHON = "python"


class SourceValidator(BaseModel):
    """
    Source code params.
    """

    model_config = ConfigDict(use_enum_values=True)

    source: str = None
    "Pointer to source code."

    handler: str = None
    "Function entrypoint."

    code: str = None
    "Source code (plain text)."

    base64: str = None
    "Source code (base64 encoded)."

    lang: SourceLang = Field(default=SourceLang.PYTHON.value)
    "Source code language (hint)."


class BuildLang(Enum):
    """
    Build language.
    """

    YAML = "yaml"


class BuildValidator(BaseModel):
    """
    Build params.
    """

    model_config = ConfigDict(use_enum_values=True)

    base64: str = None
    "Argo workflow (base64 encoded)."

    lang: BuildLang = Field(default=BuildLang.YAML.value)
    "Argo workflow language (hint)."
