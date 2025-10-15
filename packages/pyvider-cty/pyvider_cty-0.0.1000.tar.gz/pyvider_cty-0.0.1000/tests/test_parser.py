# tests/test_parser.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from pyvider.cty.exceptions import CtyValidationError
from pyvider.cty.parser import parse_tf_type_to_ctytype
from pyvider.cty.types import (
    CtyBool,
    CtyDynamic,
    CtyList,
    CtyMap,
    CtyNumber,
    CtyObject,
    CtySet,
    CtyString,
    CtyTuple,
)

valid_test_cases = [
    ("string", CtyString()),
    ("number", CtyNumber()),
    ("bool", CtyBool()),
    ("dynamic", CtyDynamic()),
    (["list", "string"], CtyList(element_type=CtyString())),
    (["set", "number"], CtySet(element_type=CtyNumber())),
    (["map", "bool"], CtyMap(element_type=CtyBool())),
    (
        ["object", {"name": "string", "enabled": "bool"}],
        CtyObject(attribute_types={"name": CtyString(), "enabled": CtyBool()}),
    ),
    (
        ["tuple", ["string", "number"]],
        CtyTuple(element_types=(CtyString(), CtyNumber())),
    ),
]

invalid_test_cases = [
    "taco",
    ["list"],
    ["list", "taco"],
    ["object", ["name", "string"]],
    ["tuple", {"name": "string"}],
    ["taco", "string"],
]


@pytest.mark.parametrize("type_spec, expected_type", valid_test_cases)
def test_valid_type_parsing(type_spec, expected_type) -> None:
    result = parse_tf_type_to_ctytype(type_spec)
    assert result.equal(expected_type)


@pytest.mark.parametrize("type_spec", invalid_test_cases)
def test_invalid_type_parsing_raises_error(type_spec) -> None:
    with pytest.raises(CtyValidationError):
        parse_tf_type_to_ctytype(type_spec)


# 🐍⛓️🤔🪄
