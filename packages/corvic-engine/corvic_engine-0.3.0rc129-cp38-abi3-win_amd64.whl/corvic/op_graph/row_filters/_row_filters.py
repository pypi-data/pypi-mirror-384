"""Filter definitions for the FilterRows op."""

from __future__ import annotations

import functools
from collections.abc import Sequence
from typing import Any, Final, overload

import more_itertools
import polars as pl
import pyarrow as pa
from google.protobuf import struct_pb2

from corvic import pa_scalar, result
from corvic.proto_wrapper import OneofProtoWrapper, ProtoParseError
from corvic_generated.orm.v1 import table_pb2
from corvic_generated.orm.v1.table_pb2 import CompareColumnToLiteralRowFilter


@overload
def from_proto(proto: table_pb2.RowFilter) -> RowFilter: ...


@overload
def from_proto(
    proto: table_pb2.CompareColumnToLiteralRowFilter,
) -> CompareColumnToLiteral: ...


@overload
def from_proto(proto: table_pb2.CombineFiltersRowFilter) -> CombineFilters: ...


def from_proto(
    proto: (
        table_pb2.RowFilter
        | table_pb2.CompareColumnToLiteralRowFilter
        | table_pb2.CombineFiltersRowFilter
    ),
) -> RowFilter:
    """Create an Op wrapper around an Op protobuf message."""
    match proto:
        case table_pb2.RowFilter():
            return _from_row_filter(proto)
        case table_pb2.CompareColumnToLiteralRowFilter():
            return CompareColumnToLiteral(
                table_pb2.RowFilter(compare_column_to_literal=proto)
            )
        case table_pb2.CombineFiltersRowFilter():
            return CombineFilters(table_pb2.RowFilter(combine_filters=proto))


class _Base(OneofProtoWrapper[table_pb2.RowFilter]):
    """Base type for all row filters."""

    @classmethod
    def oneof_name(cls) -> str:
        return "filter"

    @classmethod
    def expected_oneof_field(cls) -> str:
        """Returns the name of field for this type in the root proto op type."""
        if cls not in _ROW_FILTER_TO_FILTER_FIELD_NAME:
            raise ProtoParseError(
                "name not registered in _ROW_FILTER_TO_FILTER_FIELD_NAME"
            )
        return _ROW_FILTER_TO_FILTER_FIELD_NAME[cls]

    def and_(self, other: RowFilter):
        return from_proto(
            table_pb2.CombineFiltersRowFilter(
                row_filters=[self._proto, other.to_proto()],
                logical_combination=table_pb2.LOGICAL_COMBINATION_ALL,
            )
        )

    def or_(self, other: RowFilter):
        return from_proto(
            table_pb2.CombineFiltersRowFilter(
                row_filters=[self._proto, other.to_proto()],
                logical_combination=table_pb2.LOGICAL_COMBINATION_ANY,
            )
        )


def _from_row_filter(proto: table_pb2.RowFilter) -> RowFilter:
    field_name = proto.WhichOneof(_Base.oneof_name())
    new_filter_type = _FILTER_FIELD_NAME_TO_ROW_FILTER.get(field_name)
    if new_filter_type is None:
        raise ProtoParseError(
            f"name not registered in _FILTER_FIELD_NAME_TO_ROW_FILTER: {field_name}"
        )
    return new_filter_type(proto)


def _make_compare_to_literal_proto(
    column_name: str,
    literal: struct_pb2.Value,
    dtype: pa.DataType,
    comparison_type: table_pb2.ComparisonType,
) -> CompareColumnToLiteralRowFilter:
    return table_pb2.CompareColumnToLiteralRowFilter(
        literal=literal,
        column_name=column_name,
        comparison_type=comparison_type,
        column_arrow_schema=pa.schema([pa.field(column_name, dtype)])
        .serialize()
        .to_pybytes(),
    )


def _make_compare_to_literal(
    column_name: str,
    literal: struct_pb2.Value,
    dtype: pa.DataType,
    comparison_type: table_pb2.ComparisonType,
) -> CompareColumnToLiteral:
    return from_proto(
        _make_compare_to_literal_proto(column_name, literal, dtype, comparison_type)
    )


LiteralType = struct_pb2.Value | float | str | bool


def eq(
    column_name: str, literal: LiteralType | None, dtype: pa.DataType
) -> CompareColumnToLiteral:
    """Include rows where column is equal to a literal."""
    return _make_compare_to_literal(
        column_name, pa_scalar.to_value(literal), dtype, table_pb2.COMPARISON_TYPE_EQ
    )


def ne(
    column_name: str, literal: LiteralType | None, dtype: pa.DataType
) -> CompareColumnToLiteral:
    """Include rows where column is not equal to a literal."""
    return _make_compare_to_literal(
        column_name, pa_scalar.to_value(literal), dtype, table_pb2.COMPARISON_TYPE_NE
    )


def lt(
    column_name: str, literal: LiteralType, dtype: pa.DataType
) -> CompareColumnToLiteral:
    """Include rows where column is less than to a literal."""
    return _make_compare_to_literal(
        column_name, pa_scalar.to_value(literal), dtype, table_pb2.COMPARISON_TYPE_LT
    )


def gt(
    column_name: str, literal: LiteralType, dtype: pa.DataType
) -> CompareColumnToLiteral:
    """Include rows where column is greater than to a literal."""
    return _make_compare_to_literal(
        column_name, pa_scalar.to_value(literal), dtype, table_pb2.COMPARISON_TYPE_GT
    )


def le(
    column_name: str, literal: LiteralType, dtype: pa.DataType
) -> CompareColumnToLiteral:
    """Include rows where column is less than or equal to than a literal."""
    return _make_compare_to_literal(
        column_name, pa_scalar.to_value(literal), dtype, table_pb2.COMPARISON_TYPE_LE
    )


def ge(
    column_name: str, literal: LiteralType, dtype: pa.DataType
) -> CompareColumnToLiteral:
    """Include rows where column is greater than or equal to to a literal."""
    return _make_compare_to_literal(
        column_name, pa_scalar.to_value(literal), dtype, table_pb2.COMPARISON_TYPE_GE
    )


def _make_combine(
    column_name: str,
    literals: Sequence[struct_pb2.Value],
    dtype: pa.DataType,
    compare: table_pb2.ComparisonType,
    logical_combination: table_pb2.LogicalCombination,
) -> CombineFilters:
    return from_proto(
        table_pb2.CombineFiltersRowFilter(
            row_filters=[
                table_pb2.RowFilter(
                    compare_column_to_literal=_make_compare_to_literal_proto(
                        column_name, literal, dtype, compare
                    )
                )
                for literal in literals
            ],
            logical_combination=logical_combination,
        )
    )


def in_(
    column_name: str,
    literals: Sequence[struct_pb2.Value | float | str | bool],
    dtype: pa.DataType,
) -> CombineFilters:
    """Include rows where column matches any value in the list of literals.

    Args:
      column_name: Name of column to compare
      literals: Literal values to compare with
      dtype: Data type of the element type of the list of literals
    """
    return _make_combine(
        column_name,
        [pa_scalar.to_value(x) for x in literals],
        dtype,
        table_pb2.COMPARISON_TYPE_EQ,
        table_pb2.LOGICAL_COMBINATION_ANY,
    )


def not_in(
    column_name: str,
    literals: Sequence[struct_pb2.Value | float | str | bool],
    dtype: pa.DataType,
) -> CombineFilters:
    """Include rows where column does not match any value in the list of literals.

    Args:
      column_name: Name of column to compare
      literals: Literal values to compare with
      dtype: Data type of the element type of the list of literals
    """
    return _make_combine(
        column_name,
        [pa_scalar.to_value(x) for x in literals],
        dtype,
        table_pb2.COMPARISON_TYPE_NE,
        table_pb2.LOGICAL_COMBINATION_ALL,
    )


class CompareColumnToLiteral(_Base):
    """A row filter that compares row values to literals."""

    @property
    def column_name(self) -> str:
        return self._proto.compare_column_to_literal.column_name

    @property
    def comparison_type(self) -> table_pb2.ComparisonType:
        return self._proto.compare_column_to_literal.comparison_type

    @functools.cached_property
    def literal_as_py(self) -> pa_scalar.PyValue:
        dtype = self.dtype
        relaxed_type = False
        if pa.types.is_integer(self.dtype):
            dtype = pa.float64()
            relaxed_type = True
        value = (
            pa_scalar.from_value(self.literal_value, dtype).unwrap_or_raise().as_py()
        )
        if relaxed_type and value is not None and int(value) == value:
            value = int(value)
        return value

    @functools.cached_property
    def literal_value(self) -> struct_pb2.Value:
        """JSON representation of literal."""
        return self._proto.compare_column_to_literal.literal

    @functools.cached_property
    def dtype(self) -> pa.DataType:
        return (
            pa.ipc.read_schema(
                pa.py_buffer(self._proto.compare_column_to_literal.column_arrow_schema)
            )
            .field(0)
            .type
        )

    def as_polars_filter(self) -> pl.Expr:
        expression = pl.col(self.column_name)
        match self.comparison_type:
            case table_pb2.COMPARISON_TYPE_EQ:
                return expression.eq(self.literal_as_py)
            case table_pb2.COMPARISON_TYPE_GE:
                return expression.ge(self.literal_as_py)
            case table_pb2.COMPARISON_TYPE_GT:
                return expression.gt(self.literal_as_py)
            case table_pb2.COMPARISON_TYPE_LE:
                return expression.le(self.literal_as_py)
            case table_pb2.COMPARISON_TYPE_LT:
                return expression.lt(self.literal_as_py)
            case table_pb2.COMPARISON_TYPE_NE:
                return expression.ne(self.literal_as_py)
            case _:
                raise result.InternalError(
                    "invalid comparison type", type=self.comparison_type
                )


class CombineFilters(_Base):
    """A row filter that combines the results of other filters."""

    @functools.cached_property
    def row_filters(self) -> Sequence[RowFilter]:
        return [
            from_proto(row_filter)
            for row_filter in self._proto.combine_filters.row_filters
        ]

    @property
    def combination_op(self) -> table_pb2.LogicalCombination:
        return self._proto.combine_filters.logical_combination

    def as_polars_filter(self) -> pl.Expr:
        if not self.row_filters:
            raise result.InternalError("no row filters present")
        expression = more_itertools.first(self.row_filters).as_polars_filter()
        for row_filter in self.row_filters[1:]:
            match self.combination_op:
                case table_pb2.LOGICAL_COMBINATION_ANY:
                    return expression.or_(row_filter.as_polars_filter())
                case table_pb2.LOGICAL_COMBINATION_ALL:
                    return expression.and_(row_filter.as_polars_filter())
                case _:
                    raise result.InternalError(
                        "invalid combination type", type=self.combination_op
                    )
        return expression


RowFilter = CompareColumnToLiteral | CombineFilters

_FILTER_FIELD_NAME_TO_ROW_FILTER: Final = {
    "compare_column_to_literal": CompareColumnToLiteral,
    "combine_filters": CombineFilters,
}

_ROW_FILTER_TO_FILTER_FIELD_NAME: Final[dict[type[Any], str]] = {
    op: name for name, op in _FILTER_FIELD_NAME_TO_ROW_FILTER.items()
}
