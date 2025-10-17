# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.workflow._base.spec import WorkflowSpec, WorkflowValidator

from digitalhub_runtime_hera.entities.workflow.hera.models import BuildValidator, SourceValidator


class WorkflowSpecHera(WorkflowSpec):
    """
    WorkflowSpecHera specifications.
    """

    def __init__(
        self,
        source: dict | None = None,
        build: dict | None = None,
        workflow: str | None = None,
    ) -> None:
        super().__init__()

        self.source = source
        self.build = build
        self.workflow = workflow


class WorkflowValidatorHera(WorkflowValidator):
    """
    WorkflowValidatorHera validator.
    """

    source: SourceValidator
    """Source code validator."""

    build: BuildValidator = None
    """Build validator."""

    workflow: str = None
    """YAML of the Workflow."""
