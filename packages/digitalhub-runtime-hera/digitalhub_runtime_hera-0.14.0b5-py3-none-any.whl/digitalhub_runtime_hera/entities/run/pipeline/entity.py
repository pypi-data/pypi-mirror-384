# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_hera.entities.run._base.entity import RunHeraRun

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_hera.entities.run.pipeline.spec import RunSpecHeraRunPipeline
    from digitalhub_runtime_hera.entities.run.pipeline.status import RunStatusHeraRunPipeline


class RunHeraRunPipeline(RunHeraRun):
    """
    RunHeraRunPipeline class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecHeraRunPipeline,
        status: RunStatusHeraRunPipeline,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecHeraRunPipeline
        self.status: RunStatusHeraRunPipeline
