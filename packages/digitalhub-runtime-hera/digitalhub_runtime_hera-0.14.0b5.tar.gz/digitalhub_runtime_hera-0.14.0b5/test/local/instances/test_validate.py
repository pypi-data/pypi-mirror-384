# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
import json
import os
from glob import glob
from pathlib import Path

import pytest
from digitalhub.factory.entity import entity_factory
from jsonschema import validate

entities_path = "test/local/instances/entities"
schemas_path = "test/local/instances/schemas"

# Build dict: kind -> path to schema file
schemas = {}
for path_to_schema in glob(f"{schemas_path}/**/*.json", recursive=True):
    kind = Path(path_to_schema).stem
    schemas[kind] = path_to_schema

# Build dict: name of file to validate -> full path to file
entity_paths = {}
for path_to_file in glob(f"{entities_path}/**/*.json", recursive=True):
    file_name = os.path.basename(path_to_file)

    # If a file in a nested directory causes a name collision, use its full path as name
    if file_name in entity_paths:
        file_name = path_to_file

    entity_paths[file_name] = path_to_file


# Build object from JSON file using factory
def build_obj(entity_file_path):
    with open(entity_file_path) as f:
        entity = json.load(f)

    kind = entity["kind"]
    spec = entity["spec"]

    built = entity_factory.build_spec(kind, **spec)
    return built.to_dict(), kind


# Validate built object against its kind's schema
def is_valid(built, kind):
    with open(schemas[kind]) as schema_file:
        schema = json.load(schema_file)

    # To validate all the properties
    schema["required"] = [a for a in list(schema["properties"].keys())]
    validate(instance=built, schema=schema)
    return True


# Tests that each JSON file contained in the specified path can successfully be
# used to generate an object through the factory, and that each generated object,
# when exported to dict, validates (through jsonschema) against its kind's schema.
class TestValidate:
    @pytest.mark.parametrize("file_name", list(entity_paths.keys()))
    def test_validate(self, file_name):
        built, kind = build_obj(f"{entity_paths[file_name]}")
        assert is_valid(built, kind)
