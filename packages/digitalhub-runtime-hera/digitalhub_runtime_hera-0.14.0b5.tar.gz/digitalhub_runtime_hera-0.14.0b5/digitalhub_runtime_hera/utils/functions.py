# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from inspect import signature
from typing import Callable

from digitalhub.utils.generic_utils import encode_string
from hera.workflows import Workflow


def run_hera_build(pipeline: Callable, *args, **kwargs) -> dict:
    """
    Build Hera pipeline as YAML.

    Parameters
    ----------
    pipeline : Callable
        Hera pipeline function.

    Returns
    -------
    dict
        Pipeline spec.
    """
    if dict(signature(pipeline).parameters):
        raise RuntimeError(f"Function {pipeline.__name__} must not have arguments.")
    workflow = pipeline()
    if not isinstance(workflow, Workflow):
        raise RuntimeError(f"Expected Hera Workflow, got {type(workflow)}. Your function must return a Hera Workflow.")
    return {"workflow": encode_string(workflow.to_yaml())}
