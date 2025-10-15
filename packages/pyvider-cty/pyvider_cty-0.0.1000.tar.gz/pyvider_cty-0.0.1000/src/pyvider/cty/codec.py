# src/pyvider/cty/codec.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from decimal import Decimal
import json
from typing import Any, cast

import msgpack  # type: ignore
from provide.foundation.errors import error_boundary

from pyvider.cty.config.defaults import (
    ERR_DECODE_DYNAMIC_TYPE,
    ERR_DECODE_REFINED_UNKNOWN,
    ERR_DYNAMIC_MALFORMED,
    ERR_OBJECT_NOT_MSGPACK_SERIALIZABLE,
    ERR_VALUE_FOR_LIST_SET,
    ERR_VALUE_FOR_MAP,
    ERR_VALUE_FOR_OBJECT,
    ERR_VALUE_FOR_TUPLE,
    MSGPACK_EXT_TYPE_CTY,
    MSGPACK_EXT_TYPE_REFINED_UNKNOWN,
    MSGPACK_RAW_FALSE,
    MSGPACK_STRICT_MAP_KEY_FALSE,
    MSGPACK_USE_BIN_TYPE_TRUE,
    REFINEMENT_COLLECTION_LENGTH_LOWER_BOUND,
    REFINEMENT_COLLECTION_LENGTH_UPPER_BOUND,
    REFINEMENT_IS_KNOWN_NULL,
    REFINEMENT_NUMBER_LOWER_BOUND,
    REFINEMENT_NUMBER_UPPER_BOUND,
    REFINEMENT_STRING_PREFIX,
    TWO_VALUE,
)
from pyvider.cty.conversion import encode_cty_type_to_wire_json
from pyvider.cty.exceptions import (
    CtyValidationError,
    DeserializationError,
    SerializationError,
)
from pyvider.cty.parser import parse_tf_type_to_ctytype
from pyvider.cty.types import (
    CtyDynamic,
    CtyList,
    CtyMap,
    CtyObject,
    CtySet,
    CtyTuple,
    CtyType,
)
from pyvider.cty.values import CtyValue
from pyvider.cty.values.markers import (
    UNREFINED_UNKNOWN,
    RefinedUnknownValue,
    UnknownValue,
)


def _decode_number_value(val: Any) -> Decimal:
    """Decode a numeric value from bytes or other format to Decimal."""
    if isinstance(val, bytes):
        return Decimal(val.decode("utf-8"))
    return Decimal(val)


def _extract_refinements_from_payload(payload: dict[int, Any]) -> dict[str, Any]:
    """Extract refinement data from a msgpack payload."""
    refinements = {}

    if REFINEMENT_IS_KNOWN_NULL in payload:
        refinements["is_known_null"] = payload[REFINEMENT_IS_KNOWN_NULL]
    if REFINEMENT_STRING_PREFIX in payload:
        refinements["string_prefix"] = payload[REFINEMENT_STRING_PREFIX]
    if REFINEMENT_NUMBER_LOWER_BOUND in payload:
        refinements["number_lower_bound"] = (
            _decode_number_value(payload[REFINEMENT_NUMBER_LOWER_BOUND][0]),
            payload[REFINEMENT_NUMBER_LOWER_BOUND][1],
        )
    if REFINEMENT_NUMBER_UPPER_BOUND in payload:
        refinements["number_upper_bound"] = (
            _decode_number_value(payload[REFINEMENT_NUMBER_UPPER_BOUND][0]),
            payload[REFINEMENT_NUMBER_UPPER_BOUND][1],
        )
    if REFINEMENT_COLLECTION_LENGTH_LOWER_BOUND in payload:
        refinements["collection_length_lower_bound"] = payload[REFINEMENT_COLLECTION_LENGTH_LOWER_BOUND]
    if REFINEMENT_COLLECTION_LENGTH_UPPER_BOUND in payload:
        refinements["collection_length_upper_bound"] = payload[REFINEMENT_COLLECTION_LENGTH_UPPER_BOUND]

    return refinements


def _decode_refined_unknown_payload(data: bytes) -> RefinedUnknownValue:
    """Decode a refined unknown value from msgpack data."""
    try:
        payload = msgpack.unpackb(data, raw=MSGPACK_RAW_FALSE, strict_map_key=MSGPACK_STRICT_MAP_KEY_FALSE)
        refinements = _extract_refinements_from_payload(payload)
        return RefinedUnknownValue(**refinements)
    except Exception as e:
        error_message = ERR_DECODE_REFINED_UNKNOWN.format(error=e)
        raise DeserializationError(error_message) from e


def _ext_hook(code: int, data: bytes) -> Any:
    match code:
        case 0:
            return UNREFINED_UNKNOWN
        case 12:
            return _decode_refined_unknown_payload(data)
        case _:
            # Per protocol, any other extension code is an unrefined unknown.
            return UNREFINED_UNKNOWN


def _serialize_unknown(value: CtyValue[Any]) -> Any:
    if not isinstance(value.value, RefinedUnknownValue):
        return msgpack.ExtType(MSGPACK_EXT_TYPE_CTY, b"")
    payload: dict[int, Any] = {}
    if value.value.is_known_null is not None:
        payload[REFINEMENT_IS_KNOWN_NULL] = value.value.is_known_null
    if value.value.string_prefix is not None:
        payload[REFINEMENT_STRING_PREFIX] = value.value.string_prefix
    if value.value.number_lower_bound is not None:
        num, inclusive = value.value.number_lower_bound
        payload[REFINEMENT_NUMBER_LOWER_BOUND] = [str(num).encode("utf-8"), inclusive]
    if value.value.number_upper_bound is not None:
        num, inclusive = value.value.number_upper_bound
        payload[REFINEMENT_NUMBER_UPPER_BOUND] = [str(num).encode("utf-8"), inclusive]
    if value.value.collection_length_lower_bound is not None:
        payload[REFINEMENT_COLLECTION_LENGTH_LOWER_BOUND] = value.value.collection_length_lower_bound
    if value.value.collection_length_upper_bound is not None:
        payload[REFINEMENT_COLLECTION_LENGTH_UPPER_BOUND] = value.value.collection_length_upper_bound
    if not payload:
        return msgpack.ExtType(MSGPACK_EXT_TYPE_CTY, b"")
    packed_payload = msgpack.packb(payload)
    return msgpack.ExtType(MSGPACK_EXT_TYPE_REFINED_UNKNOWN, packed_payload)


def _serialize_dynamic(value: CtyValue[Any]) -> list[Any]:
    inner_value = value.value
    if not isinstance(inner_value, CtyValue):
        raise SerializationError(
            ERR_DYNAMIC_MALFORMED,
            value=value,
        )

    actual_type = inner_value.type
    serializable_inner = _convert_value_to_serializable(inner_value, actual_type)

    type_spec_json = encode_cty_type_to_wire_json(actual_type)
    type_spec_bytes = json.dumps(type_spec_json, separators=(",", ":")).encode("utf-8")
    return [type_spec_bytes, serializable_inner]


def _serialize_object_value(inner_val: Any, schema: CtyObject) -> dict[str, Any]:
    """Serialize a CtyObject value."""
    if not isinstance(inner_val, dict):
        raise TypeError(ERR_VALUE_FOR_OBJECT)
    return {
        k: _convert_value_to_serializable(v, schema.attribute_types[k]) for k, v in sorted(inner_val.items())
    }


def _serialize_map_value(inner_val: Any, schema: CtyMap[Any]) -> dict[str, Any]:
    """Serialize a CtyMap value."""
    if not isinstance(inner_val, dict):
        raise TypeError(ERR_VALUE_FOR_MAP)
    return {k: _convert_value_to_serializable(v, schema.element_type) for k, v in sorted(inner_val.items())}


def _serialize_collection_value(inner_val: Any, schema: CtyList[Any] | CtySet[Any]) -> list[Any]:
    """Serialize a CtyList or CtySet value."""
    if not hasattr(inner_val, "__iter__"):
        raise TypeError(ERR_VALUE_FOR_LIST_SET)
    items = (
        sorted(list(inner_val), key=lambda v: v._canonical_sort_key())
        if isinstance(schema, CtySet)
        else inner_val
    )
    return [_convert_value_to_serializable(item, schema.element_type) for item in items]


def _serialize_tuple_value(inner_val: Any, schema: CtyTuple) -> list[Any]:
    """Serialize a CtyTuple value."""
    if not isinstance(inner_val, tuple):
        raise TypeError(ERR_VALUE_FOR_TUPLE)
    return [_convert_value_to_serializable(item, schema.element_types[i]) for i, item in enumerate(inner_val)]


def _serialize_decimal_value(decimal_val: Decimal) -> int | float | str:
    """Serialize a Decimal value for MessagePack encoding.

    Returns int for integers in int64 range, str for large integers, or float for non-integers.
    For non-integers, checks if float conversion would lose precision and encodes as string if so.
    """
    try:
        # Check if it's a whole number
        is_integer = decimal_val % 1 == 0
    except Exception:
        # For extremely large numbers, check using as_tuple()
        _sign, _digits, exponent = decimal_val.as_tuple()
        is_integer = isinstance(exponent, int) and exponent >= 0

    if is_integer:
        int_val = int(decimal_val)
        # MessagePack only supports int64 range natively (-2^63 to 2^63-1)
        # For values outside this range, encode as string (matches go-cty behavior)
        if -(2**63) <= int_val < 2**63:
            return int_val
        else:
            return str(int_val)
    else:
        # For non-integers, check if converting to float would lose precision
        # This matches go-cty's behavior of preserving exact decimal values
        float_val = float(decimal_val)

        # Strategy: Detect if the Decimal has float artifacts (from being created via Decimal(float))
        # vs being created from a clean source like Decimal("123.456789012345678901234567890").
        #
        # Float artifacts look like very long decimal expansions (e.g., ...28421709430404...)
        # that come from binary floating point representation.
        #
        # Key insight: If the decimal's string representation has many digits (>16 significant figures
        # after decimal point) and differs from the float's string representation, it's likely artifacts.

        original_str = str(decimal_val)
        float_str = str(float_val)

        # Check if the original string has float artifacts (very long precision)
        # Float64 has ~15-17 significant decimal digits. If we see more than 20 digits after
        # the decimal point, it's likely float representation artifacts.
        if "." in original_str:
            decimal_part = original_str.split(".")[1]
            if len(decimal_part) > 20:
                # This looks like float artifacts - just use the float
                return float_val

        # Convert float back to Decimal via its string representation to check precision loss
        roundtrip_decimal = Decimal(float_str)

        # If round-trip through float preserves the value, no precision loss
        if decimal_val == roundtrip_decimal:
            return float_val

        # If the string representations are equal, use float (they're equivalent)
        if original_str == float_str:
            return float_val

        # Otherwise, preserve as string to maintain precision beyond float64
        return str(decimal_val)


def _convert_value_to_serializable(value: CtyValue[Any], schema: CtyType[Any]) -> Any:
    if not isinstance(value, CtyValue):
        value = schema.validate(value)
    if value.is_unknown:
        return _serialize_unknown(value)
    if value.is_null:
        return None
    if isinstance(schema, CtyDynamic):
        return _serialize_dynamic(value)

    inner_val = value.value
    if isinstance(schema, CtyObject):
        return _serialize_object_value(inner_val, schema)
    if isinstance(schema, CtyMap):
        return _serialize_map_value(inner_val, schema)
    if isinstance(schema, CtyList | CtySet):
        return _serialize_collection_value(inner_val, cast(CtyList[Any] | CtySet[Any], schema))
    if isinstance(schema, CtyTuple):
        return _serialize_tuple_value(inner_val, schema)
    if isinstance(inner_val, Decimal):
        return _serialize_decimal_value(inner_val)
    return inner_val


def _msgpack_default_handler(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return _serialize_decimal_value(obj)
    error_message = ERR_OBJECT_NOT_MSGPACK_SERIALIZABLE.format(type_name=type(obj).__name__)
    raise TypeError(error_message)


def cty_to_msgpack(value: CtyValue[Any], schema: CtyType[Any]) -> bytes:
    with error_boundary(
        context={
            "operation": "cty_to_msgpack_serialization",
            "value_type": type(value).__name__,
            "schema_type": str(schema),
            "value_is_null": value.is_null if hasattr(value, "is_null") else False,
            "value_is_unknown": value.is_unknown if hasattr(value, "is_unknown") else False,
        }
    ):
        serializable_data = _convert_value_to_serializable(value, schema)
        return msgpack.packb(
            serializable_data,
            default=_msgpack_default_handler,
            use_bin_type=MSGPACK_USE_BIN_TYPE_TRUE,
        )


def _unpacked_to_cty(data: Any, schema: CtyType[Any]) -> CtyValue[Any]:
    if isinstance(data, UnknownValue):
        return CtyValue.unknown(schema, value=data)
    if data is None:
        return CtyValue.null(schema)
    return schema.validate(data)


def cty_from_msgpack(data: bytes, cty_type: CtyType[Any]) -> CtyValue[Any]:
    with error_boundary(
        context={
            "operation": "cty_from_msgpack_deserialization",
            "data_size": len(data),
            "schema_type": str(cty_type),
            "is_dynamic_type": isinstance(cty_type, CtyDynamic),
        }
    ):
        if not data:
            return CtyValue.null(cty_type)
        raw_unpacked = msgpack.unpackb(
            data,
            ext_hook=_ext_hook,
            raw=MSGPACK_RAW_FALSE,
            strict_map_key=MSGPACK_STRICT_MAP_KEY_FALSE,
        )

        if (
            isinstance(cty_type, CtyDynamic)
            and isinstance(raw_unpacked, list)
            and len(raw_unpacked) == TWO_VALUE
            and isinstance(raw_unpacked[0], bytes)
        ):
            try:
                type_spec = json.loads(raw_unpacked[0].decode("utf-8"))
                actual_type = parse_tf_type_to_ctytype(type_spec)
                inner_value = _unpacked_to_cty(raw_unpacked[1], actual_type)
                return CtyValue(vtype=cty_type, value=inner_value)
            except json.JSONDecodeError as e:
                raise DeserializationError(ERR_DECODE_DYNAMIC_TYPE) from e
            except CtyValidationError as e:
                raise e

        return _unpacked_to_cty(raw_unpacked, cty_type)


# 🐍⛓️🤔🪄
