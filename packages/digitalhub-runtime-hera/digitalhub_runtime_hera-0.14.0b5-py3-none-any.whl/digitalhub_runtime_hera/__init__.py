# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
from digitalhub_runtime_hera.entities._commons.enums import EntityKinds
from digitalhub_runtime_hera.entities.run.build.builder import RunHeraRunBuildBuilder
from digitalhub_runtime_hera.entities.run.pipeline.builder import RunHeraRunPipelineBuilder
from digitalhub_runtime_hera.entities.task.build.builder import TaskHeraBuildBuilder
from digitalhub_runtime_hera.entities.task.pipeline.builder import TaskHeraPipelineBuilder
from digitalhub_runtime_hera.entities.workflow.hera.builder import WorkflowHeraBuilder

entity_builders = (
    (EntityKinds.WORKFLOW_HERA.value, WorkflowHeraBuilder),
    (EntityKinds.TASK_HERA_PIPELINE.value, TaskHeraPipelineBuilder),
    (EntityKinds.TASK_HERA_BUILD.value, TaskHeraBuildBuilder),
    (EntityKinds.RUN_HERA_BUILD.value, RunHeraRunBuildBuilder),
    (EntityKinds.RUN_HERA_PIPELINE.value, RunHeraRunPipelineBuilder),
)

try:
    from digitalhub_runtime_hera.runtimes.builder import RuntimeHeraBuilder

    runtime_builders = ((kind, RuntimeHeraBuilder) for kind in [e.value for e in EntityKinds])
except ImportError:
    runtime_builders = tuple()
