# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.runtimes.builder import RuntimeBuilder

from digitalhub_runtime_hera.runtimes.runtime import RuntimeHera


class RuntimeHeraBuilder(RuntimeBuilder):
    """RuntaimeHeraBuilder class."""

    RUNTIME_CLASS = RuntimeHera
