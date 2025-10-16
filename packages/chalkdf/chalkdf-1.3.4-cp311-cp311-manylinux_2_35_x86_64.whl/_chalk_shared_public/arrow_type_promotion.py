from typing import Any, Callable, Sequence, TypeVar, cast

import pyarrow as pa
from chalk.utils.collections import OrderedSet

from libchalk.chalkfunction import (
    ArgumentType,
    CallbackType,
    DataFrameParameterType,
    default_arrow_type_promoter,
)

pa_int_types = {8: pa.int8(), 16: pa.int16(), 32: pa.int32(), 64: pa.int64()}
pa_uint_types = {8: pa.uint8(), 16: pa.uint16(), 32: pa.uint32(), 64: pa.uint64()}
pa_float_types = {16: pa.float16(), 32: pa.float32(), 64: pa.float64()}
pa_date_types = {32: pa.date32(), 64: pa.date64()}
datetime_type = pa.timestamp("us", "UTC")
datetime_type_no_tz = pa.timestamp("us")
duration_type = pa.duration("us")


def _most_precise_type_lists_arrow(
    *,
    types: Sequence[pa.DataType],
    minimum_type: pa.DataType | None,
    enforce_equal_list_size: bool = False,
) -> pa.DataType:
    """
    Returns the most precise numeric type which encompasses all inputs, promoting if needed.

    If `enforce_equal_list_size` is True, then all inputs must be of type FixedSizeListType
    and have the same list size.
    """

    list_element_types: list[pa.DataType] = []
    list_element_sizes: list[int] = []
    for input_type in types:
        if not isinstance(input_type, (pa.FixedSizeListType, pa.ListType, pa.LargeListType)):
            raise ValueError(f"Expected scalar list type, got operand type '{input_type}'")

        if enforce_equal_list_size:
            if not isinstance(input_type, pa.FixedSizeListType):
                raise ValueError(f"Expected scalar fixed size list type, got operand type '{input_type}'")
            list_element_sizes.append(input_type.list_size)

        list_element_types.append(input_type.value_type)

    if enforce_equal_list_size and len(set(list_element_sizes)) > 1:
        raise ValueError("Expected all operands of input to be of the same length")

    return promote_types_from_arrow(types=list_element_types, minimum_type=minimum_type)


def _most_precise_type_structs_arrow(
    *,
    types: Sequence[pa.DataType],
    minimum_type: pa.DataType | None,
    enforce_complete_structs: bool = False,
) -> pa.DataType:
    """
    Returns the most precise numeric type which encompasses all inputs, promoting if needed.

    If `enforce_equal_struct_size` is True, then all datatypes must contain every field in every other datatype.
    """

    mapping_of_field_types: dict[str, list[pa.DataType]] = {}
    for input_type in types:
        if not isinstance(input_type, pa.StructType):
            raise ValueError(f"Expected struct type, got operand type '{input_type}'")
        for field in input_type:
            if field.name not in mapping_of_field_types:
                mapping_of_field_types[field.name] = []
            mapping_of_field_types[field.name].append(field.type)
    if enforce_complete_structs:
        for field_name, field_types in mapping_of_field_types.items():
            if len(field_types) != len(types):
                raise ValueError(f"Expected all struct operands of input to contain field '{field_name}'")

    if minimum_type is not None:
        if not isinstance(minimum_type, pa.StructType):
            raise ValueError(f"Expected minimum type to be struct type, got operand type '{minimum_type}'")
        for field in minimum_type:
            if field.name not in mapping_of_field_types:
                mapping_of_field_types[field.name] = []
            mapping_of_field_types[field.name].append(field.type)

    new_fields = {
        field: promote_types_from_arrow(types=field_types, minimum_type=None)
        for field, field_types in mapping_of_field_types.items()
    }
    return pa.struct(new_fields)


def most_precise_numeric_type_from_arrow(
    *,
    types: Sequence[pa.DataType],
    minimum_type: pa.DataType | None = None,
) -> pa.DataType:
    if minimum_type is not None:
        types = [z for z in types] + [minimum_type]

    for t in types:
        if (
            t not in pa_int_types.values()
            and t not in pa_uint_types.values()
            and t not in pa_float_types.values()
            and t not in pa_date_types.values()
            and t != datetime_type
            and t != duration_type
            and not (pa.types.is_fixed_size_list(t) and t.value_type in pa_float_types.values())
        ):
            raise ValueError(f"Expected numeric type, got {t}")
        if t == datetime_type_no_tz:
            raise ValueError("UTC Timezone must be specified on your timestamp objects")

    if (
        all(pa.types.is_fixed_size_list(t) and t.value_type in pa_float_types.values() for t in types)
        and len(types) > 0
    ):
        first_type = types[0]
        # Included to help pyright understand types.
        assert pa.types.is_fixed_size_list(first_type), f"Expected FixedSizeListType but got {first_type}"
        fixed_t: pa.FixedSizeListType = first_type
        return pa.list_(fixed_t.value_type, fixed_t.list_size)

    if all(t in pa_float_types.values() for t in types):
        return pa_float_types[max(t.bit_width for t in types)]

    elif all(t in pa_uint_types.values() for t in types):
        return pa_uint_types[max(t.bit_width for t in types)]

    elif all(t in pa_date_types.values() for t in types):
        # same as chalk/features/_encoding/pyarrow.py::rich_to_pyarrow timedelta
        return pa.duration("us")

    elif all(t == datetime_type for t in types):
        # same as chalk/features/_encoding/pyarrow.py::rich_to_pyarrow timedelta
        return pa.duration("us")

    elif len(types) == 2 and types[0] == datetime_type and types[1] == duration_type:
        # TODO: need to check that the operation type is subtraction
        # Currently errors downstream, so not urgent
        return pa.timestamp("us", "UTC")

    elif any(t == datetime_type for t in types):
        raise ValueError("Only subtraction is supported on datetime types")

    elif any(t in pa_date_types.values() for t in types):
        raise ValueError("Only subtraction is supported on date types")

    elif any(t in pa_float_types.values() for t in types):
        return pa.float64()

    elif (max_int_type := max(t.bit_width for t in types)) in pa_int_types:
        return pa_int_types[max_int_type]

    else:
        raise ValueError(
            (
                f"Unsupported numeric type for {types}. "
                f"Expected int with bit width in {tuple(pa_int_types.keys())}, got {max_int_type}"
            )
        )


T = TypeVar("T")


def cast_elements_to_arrow_type(
    *,
    types: Sequence[T],
    target_types: Sequence[ArgumentType],
    cast_fn: Callable[[T, pa.DataType], T],
    extract_dtype: Callable[[T], pa.DataType | CallbackType],
    lit: Callable[[Any, pa.DataType], T],
) -> list[T]:
    if len(types) != len(target_types):
        raise ValueError(
            f"Length of types and target_types must be equal. Got {len(types)} input types and {len(target_types)} target types"
        )

    promoted_operands: list[T] = []
    for target, e in zip(target_types, types):
        if isinstance(target, CallbackType):
            # Callback arguments cannot be promoted.
            promoted_operands.append(e)
        elif isinstance(target, DataFrameParameterType):
            # DataFrame parameter type arguments cannot be promoted.
            promoted_operands.append(e)
        elif extract_dtype(e) == pa.null():
            # Null inputs are always replaced by the literal null.
            promoted_operands.append(lit(None, target))
        elif extract_dtype(e) == target:
            # The argument type already matches the overload target type.
            promoted_operands.append(e)
        else:
            # In order to compute this underscore expression, an implicit cast is
            # required. Therefore, cast the argument before the function is called.
            promoted_operands.append(cast_fn(e, target))
    return promoted_operands


def promote_types_from_arrow(
    types: Sequence[pa.DataType],
    minimum_type: pa.DataType | None,
) -> pa.DataType:
    types_without_minimum = types
    types_with_minimum: list[pa.DataType] = (
        [z for z in types] + [minimum_type] if minimum_type is not None else [z for z in types]
    )
    del types
    non_null_underlying_input_types = list(OrderedSet([x for x in types_with_minimum if not pa.types.is_null(x)]))

    if len(non_null_underlying_input_types) == 1:
        return non_null_underlying_input_types[0]
    if len(types_with_minimum) == 1:
        return types_with_minimum[0]
    if all(pa.types.is_fixed_size_list(t) for t in types_with_minimum):
        most_precise_list_type = _most_precise_type_lists_arrow(
            types=types_without_minimum,
            minimum_type=minimum_type,
            enforce_equal_list_size=True,
        )
        list_size = cast(pa.FixedSizeListType, types_with_minimum[0]).list_size
        return pa.list_(most_precise_list_type, list_size)
    if all(
        pa.types.is_list(t) or pa.types.is_large_list(t) or pa.types.is_fixed_size_list(t) for t in types_with_minimum
    ):
        most_precise_list_type = _most_precise_type_lists_arrow(
            types=types_without_minimum,
            minimum_type=minimum_type,
            enforce_equal_list_size=False,
        )
        return pa.large_list(most_precise_list_type)
    if all(pa.types.is_struct(t) for t in types_with_minimum):
        return _most_precise_type_structs_arrow(
            types=types_without_minimum,
            minimum_type=minimum_type,
            enforce_complete_structs=False,
        )

    if any(t == datetime_type_no_tz for t in types_with_minimum):
        raise ValueError("UTC Timezone must be specified on your timestamp objects")

    if all(pa.types.is_string(t) or pa.types.is_large_string(t) for t in types_with_minimum):
        return pa.large_utf8()
    elif any(pa.types.is_string(t) or pa.types.is_large_string(t) for t in types_with_minimum):
        other_types = [t for t in types_with_minimum if not pa.types.is_string(t) and not pa.types.is_large_string(t)]
        raise ValueError(f"Cannot implicitly convert between string and other type(s): {other_types}")

    if all(pa.types.is_binary(t) or pa.types.is_large_binary(t) for t in types_with_minimum):
        return pa.large_binary()
    elif any(pa.types.is_binary(t) or pa.types.is_large_binary(t) for t in types_with_minimum):
        other_types = [t for t in types_with_minimum if not pa.types.is_binary(t) and not pa.types.is_large_binary(t)]
        raise ValueError(f"Cannot implicitly convert between binary and other type(s): {other_types}")

    if all(pa.types.is_boolean(t) for t in types_with_minimum):
        return pa.bool_()

    if all(t in pa_date_types.values() for t in types_with_minimum):
        # same as chalk/features/_encoding/pyarrow.py::rich_to_pyarrow date
        return pa.date64()
    elif any(t in pa_date_types.values() for t in types_with_minimum):
        raise ValueError("Only subtraction is supported on date types")

    if all(t == datetime_type for t in types_with_minimum):
        return datetime_type
    elif any(t == datetime_type for t in types_with_minimum):
        raise ValueError("Only subtraction is supported on datetime types")

    return most_precise_numeric_type_from_arrow(
        types=types_without_minimum,
        minimum_type=minimum_type,
    )


def can_promote_by_casting(src: ArgumentType, target: ArgumentType) -> bool:
    # TODO inline?
    return default_arrow_type_promoter.can_promote(from_type=src, to_type=target)
