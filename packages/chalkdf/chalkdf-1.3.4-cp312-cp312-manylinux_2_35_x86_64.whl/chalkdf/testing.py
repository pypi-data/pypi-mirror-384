"""Testing utilities for :mod:`chalkdf`."""

from __future__ import annotations

import json
import math
import typing

import pyarrow
import pyarrow.compute as pc
from dateutil.parser import parse

from .dataframe import DataFrame


class Testing:
    """Assertion helpers for ``DataFrame`` objects."""

    @staticmethod
    def assert_frame_equal(
        left: DataFrame,
        right: DataFrame,
        *,
        check_row_order: bool = True,
        check_column_order: bool = True,
        check_dtype: bool = True,
        atol: float = 0.0,
        rtol: float = 0.0,
        null_equal: bool = True,
        nan_equal: bool = True,
        msg: str | None = None,
    ) -> None:
        """
        Assert that two DataFrames are equal, similar to polars.testing.assert_frame_equal.

        Parameters
        - left/right: DataFrames to compare.
        - check_row_order: If False, ignores row order by sorting on all columns.
        - check_column_order: If False, aligns by column name ignoring order.
        - check_dtype: If True, requires matching pyarrow types per column.
        - atol/rtol: Tolerances for approximate float equality.
        - null_equal: If True, treats nulls (None) as equal.
        - nan_equal: If True, treats NaN as equal to NaN for float comparisons.
        - msg: Optional message prefix for assertion failures.
        """

        def _prefix(m: str) -> str:
            return (msg + ": " if msg else "") + m

        # Materialize both DataFrames to Arrow Tables
        def _to_table(df: DataFrame) -> pyarrow.Table:
            batches = list(df.run())
            return pyarrow.Table.from_batches(batches) if len(batches) > 0 else pyarrow.table({})

        left_tbl = _to_table(left)
        right_tbl = _to_table(right)

        # Compare column sets and determine comparison order
        left_cols = list(left_tbl.schema.names)
        right_cols = list(right_tbl.schema.names)

        if check_column_order:
            if left_cols != right_cols:
                raise AssertionError(_prefix(f"Column order/name mismatch: left={left_cols}, right={right_cols}"))
            compare_cols = left_cols
        else:
            if set(left_cols) != set(right_cols):
                raise AssertionError(
                    _prefix(f"Column set mismatch: left={sorted(left_cols)}, right={sorted(right_cols)}")
                )
            # Choose a deterministic order for comparison
            compare_cols = sorted(left_cols)
            left_tbl = left_tbl.select(compare_cols)
            right_tbl = right_tbl.select(compare_cols)

        # Optional dtype check
        if check_dtype:
            left_types = [left_tbl.schema.field(n).type for n in compare_cols]
            right_types = [right_tbl.schema.field(n).type for n in compare_cols]
            if left_types != right_types:
                pairs = [(n, lt, rt) for n, lt, rt in zip(compare_cols, left_types, right_types) if lt != rt]
                raise AssertionError(
                    _prefix("Dtype mismatch: " + ", ".join([f"{n}: {lt} != {rt}" for n, lt, rt in pairs]))
                )

        # If ignoring row order, sort both tables by all compare columns
        if not check_row_order and len(compare_cols) > 0 and len(left_tbl) > 0:
            sort_keys = [(c, "ascending") for c in compare_cols]
            left_idx = pc.sort_indices(left_tbl, sort_keys=sort_keys)
            right_idx = pc.sort_indices(right_tbl, sort_keys=sort_keys)
            left_tbl = left_tbl.take(left_idx)
            right_tbl = right_tbl.take(right_idx)

        # Compare row counts
        if len(left_tbl) != len(right_tbl):
            raise AssertionError(_prefix(f"Row count mismatch: left={len(left_tbl)} right={len(right_tbl)}"))

        n_rows = len(left_tbl)

        # Helper to compare two scalar values with tolerance and null/NaN semantics
        def _values_equal(a: typing.Any, b: typing.Any) -> bool:
            if a is None or b is None:
                return null_equal and (a is None and b is None)
            # Floats with tolerance and NaN handling
            if isinstance(a, float) or isinstance(b, float):
                # Normalize to float; non-floats cast if possible
                try:
                    af = float(a)
                    bf = float(b)
                except Exception:
                    return False
                if math.isnan(af) or math.isnan(bf):
                    return nan_equal and math.isnan(af) and math.isnan(bf)
                # Use math.isclose for tolerance checks
                return math.isclose(af, bf, rel_tol=rtol, abs_tol=atol)
            if isinstance(a, str) and isinstance(b, str):
                try:
                    date_a = parse(a)
                    date_b = parse(b)
                    if date_a.tzinfo and not date_b.tzinfo:
                        date_b = date_b.replace(tzinfo=date_a.tzinfo)
                    elif date_b.tzinfo and not date_a.tzinfo:
                        date_a = date_a.replace(tzinfo=date_b.tzinfo)
                    if date_a == date_b:
                        return True
                except:  # noqa: E722
                    return a == b
            if isinstance(a, dict) or isinstance(b, dict):
                try:
                    a = a if isinstance(a, dict) else json.loads(a)
                    b = b if isinstance(b, dict) else json.loads(b)
                    for k in a.keys():
                        if k in b.keys():
                            if not _values_equal(a[k], b[k]):
                                return False
                        else:
                            return False
                    return True
                except:  # noqa: E722
                    return False
            return a == b

        # Compare per column and per row, stop on first mismatch with context
        for col_name in compare_cols:
            left_arr = left_tbl[col_name].to_pylist()
            right_arr = right_tbl[col_name].to_pylist()

            # Fast path: exact match
            if atol == 0.0 and rtol == 0.0 and null_equal and nan_equal:
                if left_arr == right_arr:
                    continue

            for i in range(n_rows):
                la = left_arr[i]
                ra = right_arr[i]
                if not _values_equal(la, ra):
                    # Show a short snippet around the mismatch
                    context_start = max(0, i - 2)
                    context_end = min(n_rows, i + 3)
                    snippet_left = left_arr[context_start:context_end]
                    snippet_right = right_arr[context_start:context_end]
                    raise AssertionError(
                        _prefix(
                            f"Value mismatch in column '{col_name}' at row {i}: left={la} right={ra}; "
                            f"context rows {context_start}:{context_end} left={snippet_left} right={snippet_right}"
                        )
                    )

        # All checks passed
        return None
