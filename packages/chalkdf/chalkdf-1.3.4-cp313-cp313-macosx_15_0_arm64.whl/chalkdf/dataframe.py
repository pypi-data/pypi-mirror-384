"""Lightweight DataFrame wrapper around Chalk's execution engine.

The :class:`DataFrame` class constructs query plans backed by ``libchalk`` and
can materialize them into Arrow tables.  It offers a minimal API similar to
other DataFrame libraries while delegating heavy lifting to the underlying
engine.
"""

from __future__ import annotations

import os
import typing
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pyarrow
from chalk.features import Underscore
from chalk.sql._internal.sql_source import BaseSQLSource
from frozendict import frozendict

from libchalk.chalktable import (
    AggExpr,
    ChalkTable,
    CompilationOptions,
    CompiledPlan,
    Expr,
    PlanRunContext,
    SchemaDescriptor,
    SortMethod,
    string_to_join_kind,
    string_to_sort_method,
)
from libchalk.metrics import InMemoryMetricsEventCollector
from libchalk.utils import InMemoryErrorCollector

from .underscore_conversion.convert_underscore_to_expr import convert_underscore_to_agg_expr, convert_underscore_to_expr

if typing.TYPE_CHECKING:
    from libchalk.chalksql import ChalkSqlCatalog  # pragma: no cover

MaterializedTable = pyarrow.RecordBatch | pyarrow.Table

_empty_table_dict = frozendict()


def _generate_table_name(prefix: str = "") -> str:
    """Generate a unique table name with an optional ``prefix``."""

    return prefix + str(uuid.uuid4())


class DataFrame:
    """Logical representation of tabular data.

    A :class:`DataFrame` wraps a :class:`~libchalk.chalktable.ChalkTable`
    plan and a mapping of materialized Arrow tables.  Operations construct new
    plans and return new ``DataFrame`` instances, leaving previous ones
    untouched.
    """

    def __init__(
        self,
        root: ChalkTable | MaterializedTable,
        tables: Dict[str, MaterializedTable] | None = None,
    ):
        """Create a ``DataFrame`` from a plan or materialized Arrow table.

        :param root: Either a ``ChalkTable`` plan or an in-memory Arrow table.
        :param tables: Mapping of additional table names to Arrow data.
        """

        super().__init__()

        if isinstance(root, MaterializedTable):
            generated_name = _generate_table_name()
            self._plan: ChalkTable = ChalkTable.named_table(
                generated_name,
                SchemaDescriptor(schema=root.schema, sorted_by=[], partitioned_by="single_threaded"),
            )
            self._tables = {generated_name: root}
        else:
            self._plan = root
            self._tables = tables or {}
        self._compiled_plan: CompiledPlan | None = None

    @classmethod
    def named_table(cls, name: str, schema: pyarrow.Schema) -> DataFrame:
        """Create a ``DataFrame`` for a named table.

        :param name: Table identifier.
        :param schema: Arrow schema describing the table.
        :return: DataFrame referencing the named table.
        """

        return cls(
            ChalkTable.named_table(
                name, SchemaDescriptor(schema=schema, sorted_by=[], partitioned_by="single_threaded")
            )
        )

    @classmethod
    def from_arrow(cls, data: MaterializedTable):
        """Construct a ``DataFrame`` from an in-memory Arrow object."""

        return cls(data)

    @classmethod
    def scan_parquet(
        cls,
        input_uris: list[str | Path],
        *,
        num_concurrent_downloads: int,
        max_num_batches_to_buffer: int,
        target_batch_size_bytes: int,
        observed_at_partition_key: str | None = None,
        schema: pyarrow.Schema | None = None,
    ) -> DataFrame:
        """
        Scan parquet files and return a DataFrame.
        :param input_uris: List of URIs to scan.
        :param schema: Schema of the data.
        :param num_concurrent_downloads: Number of concurrent downloads.
        :param max_num_batches_to_buffer: Maximum number of batches to buffer.
        :param target_batch_size_bytes: Target batch size in bytes.
        :param observed_at_partition_key: Partition key for observed_at.
        :return: DataFrame
        """
        # Accept filesystem paths or URIs; normalize to proper URIs for libchalk.
        # Accept filesystem paths, URIs, and hive-style patterns.
        #
        # - URIs (contain "://"): pass through unchanged.
        # - Hive/glob patterns (contain wildcards or partition tokens):
        #   pass through as POSIX paths (no scheme) to mirror C++ behavior
        #   and avoid any encoding of '=' in partition directories.
        # - Plain local files/dirs: convert to file:// URIs without encoding.
        normalized: list[str] = []
        for p in input_uris:
            s = p if isinstance(p, str) else str(p)
            if "://" in s:
                normalized.append(s)
                continue
            # Detect hive/glob patterns
            if any(token in s for token in ("*", "?", "[", ":user_id", "=:", ":")):
                # Keep as absolute POSIX path without scheme
                normalized.append(str(Path(s).resolve()))
                continue
            # Plain path -> file:// URI without percent-encoding
            abs_path = str(Path(s).resolve())
            if not abs_path.startswith("/"):
                normalized.append(Path(s).resolve().as_uri())
            else:
                normalized.append("file://" + abs_path)
        plan = ChalkTable.scan_parquet(
            normalized,
            schema,
            num_concurrent_downloads,
            max_num_batches_to_buffer,
            target_batch_size_bytes,
            observed_at_partition_key,
        )
        return cls(plan, {})

    @classmethod
    def scan(
        cls,
        name: str,
        input_uris: list[str | Path],
        schema: pyarrow.Schema,
    ) -> DataFrame:
        """
        Scan files and return a DataFrame. Currently, CSV (with headers) and Parquet are supported.
        :param name: A name to call the table being scanned.
        :param input_uris: List of URIs to scan.
        :param schema: Schema of the data.
        :return: DataFrame
        """
        # Accept filesystem paths or URIs; construct file:// URIs manually for
        # local paths to avoid percent-encoding partition tokens like '='.
        normalized: list[str] = []
        for p in input_uris:
            s = p if isinstance(p, str) else str(p)
            if "://" in s:
                normalized.append(s)
            else:
                abs_path = str(Path(s).resolve())
                if not abs_path.startswith("/"):
                    normalized.append(Path(s).resolve().as_uri())
                else:
                    normalized.append("file://" + abs_path)
        plan = ChalkTable.table_scan(name, normalized, schema)
        return cls(plan, {})

    @classmethod
    def table_scan_parquet(
        cls,
        name: str,
        input_uris: list[str | Path],
        *,
        schema: pyarrow.Schema | None = None,
    ) -> DataFrame:
        """
        Scan parquet files and return a DataFrame.
        :param name: A name to call the table being scanned.
        :param input_uris: List of URIs to scan.
        :param schema: Schema of the data.
        :return: DataFrame
        """
        # Accept filesystem paths or URIs; construct file:// URIs manually for
        # local paths to avoid percent-encoding partition tokens like '='.
        normalized: list[str] = []
        for p in input_uris:
            s = p if isinstance(p, str) else str(p)
            if "://" in s:
                normalized.append(s)
            else:
                abs_path = str(Path(s).resolve())
                if not abs_path.startswith("/"):
                    normalized.append(Path(s).resolve().as_uri())
                else:
                    normalized.append("file://" + abs_path)
        plan = ChalkTable.table_scan_parquet(name, normalized, schema)
        return cls(plan, {})

    @classmethod
    def scan_glue_iceberg(
        cls,
        glue_table_name: str,
        schema: typing.Mapping[str, pyarrow.DataType],
        *,
        batch_row_count: int = 1_000,
        aws_catalog_account_id: typing.Optional[str] = None,
        aws_catalog_region: typing.Optional[str] = None,
        aws_role_arn: typing.Optional[str] = None,
        filter_predicate: typing.Optional[Expr] = None,
        parquet_scan_range_column: typing.Optional[str] = None,
        custom_partitions: typing.Optional[dict[str, tuple[typing.Literal["date_trunc(day)"], str]]] = None,
        partition_column: typing.Optional[str] = None,
    ) -> DataFrame:
        """Load data from an AWS Glue Iceberg table.

        :param glue_table_name: Fully qualified ``database.table`` name.
        :param schema: Mapping of column names to Arrow types.
        :param batch_row_count: Number of rows per batch.
        :param aws_catalog_account_id: AWS account hosting the Glue catalog.
        :param aws_catalog_region: Region of the Glue catalog.
        :param aws_role_arn: IAM role to assume for access.
        :param filter_predicate: Optional filter applied during scan.
        :param parquet_scan_range_column: Column used for range-based reads.
        :param custom_partitions: Additional partition definitions.
        :param partition_column: Column name representing partitions.
        :return: DataFrame backed by the Glue table.
        """

        custom_partitions = {} if custom_partitions is None else custom_partitions
        custom_partitions = {
            partition_column: tuple(partition_definition)  # pyright: ignore
            for partition_column, partition_definition in custom_partitions.items()
        }
        filter_predicate = (
            Expr.lit(pyarrow.scalar(True, type=pyarrow.bool_())) if filter_predicate is None else filter_predicate
        )

        plan = ChalkTable.load_glue_table(
            aws_catalog_account_id=aws_catalog_account_id,
            aws_catalog_region=aws_catalog_region,
            aws_role_arn=aws_role_arn,
            table_name=list(glue_table_name.split(".")),
            schema=pyarrow.schema(schema),
            batch_row_count=batch_row_count,
            filter_predicate=filter_predicate,
            parquet_scan_range_column=parquet_scan_range_column or partition_column,
            custom_partitions=custom_partitions or {},
        )

        return cls(plan, {})

    @classmethod
    def from_catalog_table(
        cls,
        table_name: str,
        *,
        catalog: "ChalkSqlCatalog",
    ) -> DataFrame:
        """Create a ``DataFrame`` from a Chalk SQL catalog table."""

        plan = ChalkTable.from_catalog_table(
            table_name,
            catalog=catalog,
        )
        return cls(plan, {})

    @classmethod
    def from_datasource(cls, source: BaseSQLSource, query: str, expected_output_schema: pyarrow.Schema):
        """
        Create a DataFrame from the result of querying a SQL source.
        :param source: SQL source to query.
        :param query: SQL query to execute.
        :param expected_output_schema: Output schema of the query result. The datasource's driver is expected
        to convert the native query result to this schema.
        """
        if not isinstance(source, BaseSQLSource):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError(f"source must be a BaseSQLSource, got {source}")
        if not isinstance(expected_output_schema, pyarrow.Schema):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError("expected_output_schema must be a pyarrow.Schema")
        plan = ChalkTable.from_datasource(source, query, expected_output_schema)
        return cls(plan)

    def _apply_function(
        self, new_plan: ChalkTable, additional_tables: typing.Mapping[str, MaterializedTable] = _empty_table_dict
    ) -> DataFrame:
        """Return a new ``DataFrame`` with ``new_plan`` and merged tables."""

        return DataFrame(new_plan, {**self._tables, **additional_tables})

    def _compile(self, *, num_threads: int = 10, recompile: bool = False) -> CompiledPlan:
        """Compile the current plan if necessary.

        :param num_threads: Number of threads used during compilation.
        :param recompile: Force recompilation even if a plan exists.
        :return: CompiledPlan ready for execution.
        """

        if self._compiled_plan is None or recompile:
            options = CompilationOptions(num_threads=num_threads, enable_filter_pushdown_optimization=True)
            # Allow overriding parquet reader implementation via env for debugging
            env_flag = os.getenv("CHALK_USE_VELOX_PARQUET_READER")
            if env_flag is not None:
                options.use_velox_parquet_reader = env_flag.lower() not in ("0", "false", "no")
            self._compiled_plan = CompiledPlan("velox", options, [self._plan])
        return self._compiled_plan

    def explain_logical(self) -> str:
        """Return a string representation of the logical plan."""

        return self._compile().explain_logical()

    def explain_physical(self) -> str:
        """Return a string representation of the physical plan."""

        return self._compile().explain_physical()

    def _run_context(self) -> PlanRunContext:
        """Construct a default :class:`PlanRunContext` for execution."""

        return PlanRunContext(
            correlation_id=None,
            environment_id="test",
            requester_id="requester_id",
            operation_id="dummy_op",
            execution_timestamp=pyarrow.scalar(datetime.now(timezone.utc), pyarrow.timestamp("us", "UTC")),
            is_online=True,
            max_samples=None,
            observed_at_lower_bound=None,
            observed_at_upper_bound=None,
            customer_metadata={},
            shard_id=0,
            extra_attributes={},
            query_context={},
            error_collector=InMemoryErrorCollector(1000),
            metrics_event_collector=InMemoryMetricsEventCollector(1000),
            chalk_metrics=None,
            batch_reporter=None,
            timeline_trace_writer=None,
            plan_metrics_storage_service=None,
            python_context=None,
        )

    def _as_agg_expr(self, underscore_or_agg_expression: AggExpr | Underscore) -> AggExpr:
        if isinstance(underscore_or_agg_expression, AggExpr):
            return underscore_or_agg_expression
        elif isinstance(underscore_or_agg_expression, Underscore):
            return convert_underscore_to_agg_expr(underscore_or_agg_expression, self.get_plan().schema_dict)
        else:
            raise ValueError(f"Expected to receive an AggExpr or Underscore, got {type(underscore_or_agg_expression)}")

    def _as_expr(self, underscore_or_expression: Expr | Underscore) -> Expr:
        if isinstance(underscore_or_expression, Expr):
            return underscore_or_expression
        elif isinstance(underscore_or_expression, Underscore):
            return convert_underscore_to_expr(underscore_or_expression, self.get_plan().schema_dict)
        else:
            raise ValueError(f"Expected to receive an Expr or Underscore, got {type(underscore_or_expression)}")

    def get_plan(self) -> ChalkTable:
        """Expose the underlying :class:`ChalkTable` plan."""

        return self._plan

    def get_tables(self) -> dict[str, MaterializedTable]:
        """Return the mapping of materialized tables for this DataFrame."""

        return self._tables

    def with_columns(self, dict: typing.Mapping[str, Expr | Underscore]) -> DataFrame:
        """Add or replace columns based on a mapping of expressions."""

        existing = self._plan.schema_dict
        stuff = {k: Expr.column(k, existing[k]) for k in existing}

        for k, v in dict.items():
            stuff[k] = self._as_expr(v)

        new_plan = self._plan.project(stuff)

        return self._apply_function(new_plan)

    def with_unique_id(self, name: str) -> DataFrame:
        """Add a monotonically increasing unique identifier column."""

        new_plan = self._plan.with_unique_id(name)
        return self._apply_function(new_plan)

    def filter(self, expr: Expr | Underscore) -> DataFrame:
        """Filter rows according to ``expr``."""

        new_plan = self._plan.filter(self._as_expr(expr))
        return self._apply_function(new_plan)

    def slice(self, start: int, length: int | None = None) -> DataFrame:
        """Return a subset of rows starting at ``start`` with optional ``length``."""

        # Can't actually express "no limit" with velox limit/offset, but this'll do.
        if length is None:
            length = (2**63) - 1
        elif length <= 0:
            raise ValueError(
                f"'length' parameter in function 'slice' must be a positive integer if specified, received {length}"
            )
        new_plan = self._plan.limit(length, start)
        return self._apply_function(new_plan)

    def col(self, column: str) -> Expr:
        """
        Get a column expression from the DataFrame.
        :param column: Column name.
        :return: Column expression.
        """
        return self.column(column)

    def column(self, column: str) -> Expr:
        """
        Get a column expression from the DataFrame.
        :param column: Column name.
        :return: Column expression.
        """
        return Expr.column(column, self._plan.schema_dict[column])

    def project(self, columns: typing.Mapping[str, Expr | Underscore]) -> DataFrame:
        """Project to the provided column expressions."""

        projections = {k: self._as_expr(v) for k, v in columns.items()}
        new_plan = self._plan.project(projections)
        return self._apply_function(new_plan)

    def select(self, *columns: str) -> DataFrame:
        """Select existing columns by name."""

        projections = {col: Expr.column(col, self._plan.schema_dict[col]) for col in columns}
        new_plan = self._plan.project(projections)
        return self._apply_function(new_plan)

    def explode(self, column: str) -> DataFrame:
        """
        Explode a column in the DataFrame.
        :param column: Column name to explode.
        :return: DataFrame with exploded column.
        """
        new_plan = self._plan.explode([column])
        return self._apply_function(new_plan)

    def join(self, other: DataFrame, on: dict[str, str] | typing.Sequence[str], how: str = "inner") -> DataFrame:
        """Join this ``DataFrame`` with another.

        :param other: Right-hand ``DataFrame``.
        :param on: Column names or mapping of left->right join keys.
        :param how: Join type (e.g. ``"inner"`` or ``"left"``).
        :return: Resulting ``DataFrame`` after the join.
        """

        if isinstance(on, dict):
            on_left = list(on.keys())
            on_right = [on[r] for r in on_left]
        else:
            on_right = on_left = list(on)
        new_plan = self._plan.join(
            other._plan, on_left, string_to_join_kind(how), right_keys=on_right, right_suffix=None
        )
        return self._apply_function(new_plan, additional_tables=other._tables)

    def agg(self, by: typing.Sequence[str], *aggregations: typing.Sequence[AggExpr | Underscore]) -> DataFrame:
        """Group by ``by`` columns and apply aggregation expressions."""

        new_plan = self._plan.aggregate_exprs([*by], [self._as_agg_expr(agg) for agg in aggregations])
        return self._apply_function(new_plan)

    def order_by(self, *columns: str | tuple[str, str]) -> DataFrame:
        """Sort the ``DataFrame`` by one or more columns."""

        sort_col: list[tuple[str, SortMethod]] = []
        for col in columns:
            if isinstance(col, str):
                sort_col.append((col, SortMethod.ASCENDING))
            else:
                sort_col.append((col[0], string_to_sort_method(col[1])))

        new_plan = self._plan.sort_by(sort_col)
        return self._apply_function(new_plan)

    def rename(self, new_names: dict[str, str]) -> DataFrame:
        """
        Rename columns in the DataFrame.
        :param new_names: Dictionary mapping old column names to new column names.
        :return: DataFrame with renamed columns.
        """
        existing = self._plan.schema_dict
        projections = {k: Expr.column(k, existing[k]) for k in existing}

        for k, v in new_names.items():
            if k not in projections:
                raise KeyError(f"Column '{k}' not found in DataFrame")

            projections[str(v)] = projections[k]
            del projections[k]

        new_plan = self._plan.project(projections)

        return self._apply_function(new_plan)

    def run(
        self, tables: typing.Mapping[str, MaterializedTable] = _empty_table_dict
    ) -> typing.Sequence[pyarrow.RecordBatch]:
        """Execute the plan and yield resulting Arrow RecordBatches."""

        return (
            self._compile()
            .run(
                self._run_context(),
                {**self._tables, **tables},
                # TODO: figure out now?
                {"__execution_ts__": pyarrow.scalar(datetime.now(tz=timezone.utc), pyarrow.timestamp("us", "UTC"))},
            )
            .result()
            .batches
        )
