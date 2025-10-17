# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.builder import RunBuilder

from digitalhub_runtime_hera.entities._base.runtime_entity.builder import RuntimeEntityBuilderHera
from digitalhub_runtime_hera.entities._commons.enums import EntityKinds
from digitalhub_runtime_hera.entities.run.build.entity import RunHeraRunBuild
from digitalhub_runtime_hera.entities.run.build.spec import RunSpecHeraRunBuild, RunValidatorHeraRunBuild
from digitalhub_runtime_hera.entities.run.build.status import RunStatusHeraRunBuild


class RunHeraRunBuildBuilder(RunBuilder, RuntimeEntityBuilderHera):
    """
    RunHeraRunBuildBuilder runer.
    """

    ENTITY_CLASS = RunHeraRunBuild
    ENTITY_SPEC_CLASS = RunSpecHeraRunBuild
    ENTITY_SPEC_VALIDATOR = RunValidatorHeraRunBuild
    ENTITY_STATUS_CLASS = RunStatusHeraRunBuild
    ENTITY_KIND = EntityKinds.RUN_HERA_BUILD.value
