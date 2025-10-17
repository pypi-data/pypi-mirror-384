# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util as imputil
import typing
from pathlib import Path
from typing import Callable

from digitalhub.entities.workflow.crud import get_workflow
from digitalhub.stores.data.api import get_store
from digitalhub.utils.generic_utils import decode_base64_string, extract_archive, requests_chunk_download
from digitalhub.utils.git_utils import clone_repository
from digitalhub.utils.logger import LOGGER
from digitalhub.utils.uri_utils import (
    get_filename_from_uri,
    has_git_scheme,
    has_remote_scheme,
    has_s3_scheme,
    has_zip_scheme,
)

if typing.TYPE_CHECKING:
    from digitalhub.entities.workflow._base.entity import Workflow


def get_dhcore_workflow(workflow_string: str) -> Workflow:
    """
    Get DHCore workflow.

    Parameters
    ----------
    workflow_string : str
        Function string.

    Returns
    -------
    Workflow
        DHCore workflow.
    """
    splitted = workflow_string.split("://")[1].split("/")
    name, uuid = splitted[1].split(":")
    LOGGER.info(f"Getting workflow {name}:{uuid}.")
    try:
        return get_workflow(name, project=splitted[0], entity_id=uuid)
    except Exception as e:
        msg = f"Error getting workflow {name}:{uuid}. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg) from e


def save_workflow_source(path: Path, source_spec: dict) -> Path:
    """
    Save workflow source.

    Parameters
    ----------
    path : Path
        Path where to save the workflow source.
    source_spec : dict
        Workflow source spec.

    Returns
    -------
    Path
        Path to the workflow source.
    """
    # Prepare path
    path.mkdir(parents=True, exist_ok=True)

    # Get relevant information
    base64 = source_spec.get("base64")
    source = source_spec.get("source")
    handler: str = source_spec["handler"]

    # Base64
    if base64 is not None:
        base64_path = path / "main.py"
        base64_path.write_text(decode_base64_string(base64))
        return base64_path

    if source is None:
        raise RuntimeError("Function source not found in spec.")

    # Git repo
    if has_git_scheme(source):
        clone_repository(path, source)

    # Http(s) or s3 presigned urls
    elif has_remote_scheme(source):
        filename = path / get_filename_from_uri(source)
        if has_zip_scheme(source):
            requests_chunk_download(source.removeprefix("zip+"), filename)
            extract_archive(path, filename)
            filename.unlink()
        else:
            requests_chunk_download(source, filename)

    # S3 path
    elif has_s3_scheme(source):
        if not has_zip_scheme(source):
            raise RuntimeError("S3 source must be a zip file with scheme zip+s3://.")
        filename = path / get_filename_from_uri(source)
        store = get_store(source.removeprefix("zip+"))
        store.get_s3_source(source, filename)
        extract_archive(path, filename)
        filename.unlink()

    # Unsupported scheme
    else:
        raise RuntimeError("Unable to collect source.")

    if ":" in handler:
        handler_parts = handler.split(":")[0].split(".")
        return Path(path, *handler_parts).with_suffix(".py")
    else:
        return path.with_suffix(".py")


def get_hera_pipeline(name: str, source: Path, handler: str) -> Callable:
    """
    Get Hera pipeline.

    Parameters
    ----------
    name : str
        Name of the workflow.
    source : str
        Source of the workflow.
    handler : str
        Handler of the workflow.

    Returns
    -------
    Callable
        Hera pipeline.
    """
    try:
        if ":" in handler:
            handler = handler.split(":")[-1]
        return import_function(source, handler)
    except Exception as e:
        msg = f"Error getting '{name}' Hera pipeline. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg) from e


def import_function(path: Path, handler: str) -> Callable:
    """
    Import a function from a module.

    Parameters
    ----------
    path : Path
        Path where the function source is located.
    handler : str
        Function name.

    Returns
    -------
    Callable
        Function.
    """
    spec = imputil.spec_from_file_location(path.stem, path)
    if spec is None:
        raise RuntimeError(f"Error loading function source from {str(path)}.")

    mod = imputil.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Error getting module loader from {str(path)}.")

    spec.loader.exec_module(mod)
    func = getattr(mod, handler)
    if not callable(func):
        raise RuntimeError(f"Handler '{handler}' is not a callable.")

    return func
