# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.runtime_entity.builder import RuntimeEntityBuilder
from digitalhub.entities._commons.utils import map_actions

from digitalhub_runtime_hera.entities._commons.enums import Actions, EntityKinds


class RuntimeEntityBuilderHera(RuntimeEntityBuilder):
    EXECUTABLE_KIND = EntityKinds.WORKFLOW_HERA.value
    TASKS_KINDS = map_actions(
        [
            (
                EntityKinds.TASK_HERA_PIPELINE.value,
                Actions.PIPELINE.value,
            ),
            (
                EntityKinds.TASK_HERA_BUILD.value,
                Actions.BUILD.value,
            ),
        ]
    )
    RUN_KINDS = map_actions(
        [
            (
                EntityKinds.RUN_HERA_PIPELINE.value,
                Actions.PIPELINE.value,
            ),
            (
                EntityKinds.RUN_HERA_BUILD.value,
                Actions.BUILD.value,
            ),
        ]
    )
