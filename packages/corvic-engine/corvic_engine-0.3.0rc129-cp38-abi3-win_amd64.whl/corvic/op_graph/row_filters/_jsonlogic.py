from collections.abc import Mapping, Sequence
from typing import Final, Literal

import more_itertools
import pyarrow as pa
from google.protobuf import json_format, struct_pb2

from corvic import result
from corvic.op_graph.row_filters._row_filters import (
    CombineFilters,
    CompareColumnToLiteral,
    RowFilter,
    eq,
    ge,
    gt,
    le,
    lt,
    ne,
)
from corvic.pa_scalar import from_value, to_value


class _Error(result.Error):
    """Internal error type."""


def _validate_column_to_literal(row_filter: CompareColumnToLiteral):
    dtype = row_filter.dtype
    if pa.types.is_integer(row_filter.dtype):
        dtype = pa.float64()
    match from_value(row_filter.literal_value, dtype):
        case result.Ok():
            pass
        case result.InvalidArgumentError() as err:
            raise _Error.from_(err)


def _validate_combine_filters(row_filter: CombineFilters):
    for f in row_filter.row_filters:
        _validate_row_filter(f)


def _validate_row_filter(row_filter: RowFilter):
    match row_filter:
        case CompareColumnToLiteral():
            _validate_column_to_literal(row_filter)
        case CombineFilters():
            _validate_combine_filters(row_filter)


def _validate(row_filter: RowFilter) -> result.Ok[RowFilter] | _Error:
    """Validate row_filter contains valid literals.

    Row filters are not validated on construction because (a) historically
    they have not been validated and (b) it would make building compound expressions
    tedious.

    validate_row_filter exists for cases where user input needs to be validated
    before continuing.
    """
    try:
        _validate_row_filter(row_filter)
    except _Error as exc:
        return exc

    return result.Ok(row_filter)


def _var_name(value: struct_pb2.Value) -> str:
    match value.WhichOneof("kind"):
        case "struct_value":
            name = value.struct_value.fields.get("var", None)
            if name is None or not name.HasField("string_value"):
                raise _Error("invalid var operation")
            return name.string_value
        case None:
            raise _Error("cannot parse value")
        case _:
            raise _Error("unexpected operation type")


def _coerce_literal(literal: struct_pb2.Value, dtype: pa.DataType) -> struct_pb2.Value:
    # Attempt to coerce the literal to the type it needs to be compared against,
    # if the types don't already align.
    match literal.WhichOneof("kind"):
        case "null_value":
            types_match = pa.types.is_null(dtype)
        case "bool_value":
            types_match = pa.types.is_boolean(dtype)
        case "list_value":
            # TODO(aneesh): inner checks for nested types
            types_match = pa.types.is_list(dtype)
        case "number_value":
            types_match = pa.types.is_integer(dtype) or pa.types.is_floating(dtype)
        case "string_value":
            types_match = pa.types.is_string(dtype)
        case "struct_value":
            # TODO(aneesh): inner checks for nested types
            types_match = pa.types.is_struct(dtype)
        case None:
            raise _Error("Unknown literal type")
    if not types_match:
        match from_value(literal, dtype):
            case result.Ok(coerced_literal):
                literal = to_value(coerced_literal)
            case err:
                raise err
    return literal


def _simple_compare(
    op: Literal["==", "!=", "<=", ">=", "<", ">"],
    operands: Sequence[struct_pb2.Value],
    column_dtypes: Mapping[str, pa.DataType],
) -> RowFilter:
    expected_literal_operands: Final = 2
    if len(operands) != expected_literal_operands:
        raise _Error("unsupported literal expression passed")
    column_name = _var_name(operands[0])

    literal = operands[1]

    dtype = column_dtypes.get(column_name, None)
    if dtype is None:
        raise _Error("unknown literal type", column_name=column_name)

    literal = _coerce_literal(literal, dtype)

    match op:
        case "==":
            return eq(column_name, literal, dtype)
        case "!=":
            return ne(column_name, literal, dtype)
        case "<=":
            return le(column_name, literal, dtype)
        case ">=":
            return ge(column_name, literal, dtype)
        case "<":
            return lt(column_name, literal, dtype)
        case ">":
            return gt(column_name, literal, dtype)


def _compound_compare(
    op: Literal["and", "or"],
    operands: Sequence[struct_pb2.Value],
    column_dtypes: Mapping[str, pa.DataType],
) -> RowFilter:
    exprs = [_parse_jsonlogic(op, column_dtypes) for op in operands]

    if len(exprs) <= 1:
        raise _Error(
            "invalid compound operation, not enough sub operations",
            op=op,
            num_sub_ops=len(exprs),
        )
    compound_op = exprs[0]
    for sub_op in exprs[1:]:
        match op:
            case "and":
                compound_op = compound_op.and_(sub_op)
            case "or":
                compound_op = compound_op.or_(sub_op)
    return compound_op


def _parse_jsonlogic(
    value: struct_pb2.Value, column_dtypes: Mapping[str, pa.DataType]
) -> RowFilter:
    match value.WhichOneof("kind"):
        case "struct_value":
            if len(value.struct_value.fields) != 1:
                raise _Error("expecting operation as key")

            op, field = more_itertools.one(value.struct_value.fields.items())

            if not field.HasField("list_value"):
                raise _Error("expecting list of operands")
            operands = field.list_value.values
        case None:
            raise _Error("cannot parse value")
        case _:
            raise _Error("unexpected operation type")

    match op:
        case "and" | "or":
            return _compound_compare(op, operands, column_dtypes)
        case "==" | "!=" | "<=" | ">=" | "<" | ">" as op:
            return _simple_compare(op, operands, column_dtypes)
        case _:
            raise _Error("unsupported row filter operation", op=op)


def parse_jsonlogic(
    expression_str: str, column_dtypes: Mapping[str, pa.DataType]
) -> result.Ok[RowFilter] | result.InvalidArgumentError:
    """Parses an expression in JsonLogic into a RowFilter.

    This function only supports the following portion of JsonLogic:

    - binary expressions only with the operators, ==, !=, >, >=, <, <= and only in the
      following form: {"<op">: [{"var": "..."}, "<literal>"].

      That is, var references are required and must be the first operand, and literals
      are required and must be the second operand.

    - n-ary operators only with the operators "and", "or" and only in the following
      form: {"<op>": [<expression>, <expression>, ...]}

    Note as a consequence of the above, "and" and "or" can only take binary expressions
    as operands.

    More information on the JsonLogic format can be found at https://jsonlogic.com

    Args:
      expression_str: Expression string to parse
      column_dtypes: Expected types of columns

    Returns:
      InvalidArgumentError: if the expression could not be parsed or is not supported
    """
    try:
        value = json_format.Parse(expression_str, struct_pb2.Value())
    except json_format.ParseError as exc:
        return result.InvalidArgumentError.from_(exc)
    try:
        row_filter = _parse_jsonlogic(value, column_dtypes)
    except _Error as exc:
        return result.InvalidArgumentError.from_(exc)

    return _validate(row_filter).or_else(
        lambda err: result.InvalidArgumentError.from_(err)
    )
