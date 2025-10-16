from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Type, cast

import pyarrow as _pa
from chalk.features._encoding.converter import PrimitiveFeatureConverter

from libchalk.chalksql import ChalkSqlCatalog
from libchalk.chalktable import ChalkTable, Expr

from .dataframe import DataFrame

_EXPR_PB: Optional[Any] = None
_GRPC_CLIENT_CLS: Optional[type] = None


if TYPE_CHECKING:
    try:
        from chalk.client.client_grpc import ChalkGRPCClient
    except ModuleNotFoundError:  # pragma: no cover - typing fallback
        ChalkGRPCClient = cast(Any, None)

    try:
        from chalk._gen.chalk.expression.v1 import expression_pb2 as expr_pb
    except ModuleNotFoundError:  # pragma: no cover - typing fallback
        expr_pb = cast(Any, None)


def _require_grpc_client(for_method: str) -> type:
    global _GRPC_CLIENT_CLS
    if _GRPC_CLIENT_CLS is not None:
        return _GRPC_CLIENT_CLS

    try:
        from chalk.client.client_grpc import ChalkGRPCClient as _ChalkGRPCClient
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"LazyFrame.{for_method} requires the Chalk gRPC client peer dependency. "
            "Install the package that provides `chalk.client.client_grpc.ChalkGRPCClient`."
        ) from exc

    _GRPC_CLIENT_CLS = _ChalkGRPCClient
    return _ChalkGRPCClient


def _require_expr_pb(for_method: str) -> Any:
    global _EXPR_PB
    if _EXPR_PB is not None:
        return _EXPR_PB

    try:
        from chalk._gen.chalk.expression.v1 import expression_pb2 as expr_pb
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            (
                f"LazyFrame.{for_method} requires the Chalk expression protos peer dependency. "
                "Install the package that provides `chalk._gen.chalk.expression.v1.expression_pb2` "
                '(e.g. `pip install "chalkdf[chalkpy]"`).'
            )
        ) from exc

    _EXPR_PB = expr_pb
    return expr_pb


# Custom stack container with Expr-aware equality for proper stack comparisons
class _LazyFrameStack(list):
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _LazyFrameStack):
            return NotImplemented
        if len(self) != len(other):
            return False

        def _compare_element(a1: Any, a2: Any):
            if isinstance(a1, list):
                if isinstance(a2, list):
                    for a1_element, a2_element in zip(a1, a2):
                        if not _compare_element(a1_element, a2_element):
                            return False
                    return True
                else:
                    return False

            if isinstance(a1, dict):
                if isinstance(a2, dict):
                    if a1.keys() != a2.keys():
                        return False
                    for key in a1:
                        if not _compare_element(a1[key], a2[key]):
                            return False
                    return True
                else:
                    return False

            if isinstance(a1, Expr) and isinstance(a2, Expr):
                if not a1._structure_equals(a2):
                    return False
                return True
            elif isinstance(a1, Expr) or isinstance(a2, Expr):
                # types mismatch, but we cant coerce to bool so we need to
                # explicitly handle it
                return False
            else:
                return a1 == a2

        # compare each function call
        for (args1, kwargs1), (args2, kwargs2) in zip(self, other):
            if len(args1) != len(args2):
                return False

            # compare args to ensure they match
            for a1, a2 in zip(args1, args2):
                if not _compare_element(a1, a2):
                    return False

            # compare kwargs with short circuiting
            if kwargs1.keys() != kwargs2.keys():
                return False
            for key in kwargs1:
                if not _compare_element(kwargs1[key], kwargs2[key]):
                    return False
        return True


class LazyFrameM(type):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the LazyFrameM instance.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        # print("LazyFrameM initialized with args:", args, "and kwargs:", kwargs)

    def __getattr__(self, item: str) -> Any:
        df = LazyFrame()
        return getattr(df, item)


class LazyFrame(metaclass=LazyFrameM):
    """
    A class representing a lazy DataFrame.

    This class is a placeholder for a lazy DataFrame implementation.
    It currently does not contain any methods or attributes.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the LazyFrame instance.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        super().__init__()

        self.stack: _LazyFrameStack = _LazyFrameStack()

    def __getattr__(self, item: str) -> Callable[..., LazyFrame]:
        def proxy(
            *args: Any,
            **kwargs: Any,
        ) -> LazyFrame:
            """
            Proxy method to handle attribute access.

            Args:
                *args: Positional arguments.
                **kwargs: Keyword arguments.
            """
            kwargs["_function_name"] = item
            self._push_call(*args, **kwargs)
            return self

        return proxy

    def _push_call(self, *args: Any, **kwargs: Any) -> None:
        """
        Push a call onto the stack.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """

        if "_function_name" not in kwargs:
            raise ValueError("_function_name is required in kwargs")

        self.stack.append((args, kwargs))

    def run(self, client: "ChalkGRPCClient") -> _pa.RecordBatch:
        client_cls = _require_grpc_client("run")
        if not isinstance(client, client_cls):
            raise TypeError("LazyFrame.run expected a ChalkGRPCClient instance.")

        res = client.execute_plan(lazy_frame_calls=self.to_proto())
        if res.errors:
            raise ValueError(res.errors)
        buffer = _pa.py_buffer(res.feather)
        reader = _pa.ipc.open_stream(buffer)
        return reader.read_next_batch()

    def _convert_to_df(self, catalog: ChalkSqlCatalog | None = None) -> DataFrame:
        el = DataFrame
        for head in self.stack:
            pos_args = head[0]
            kwargs = dict(head[1])
            if (fn := kwargs.get("_function_name", None)) is None:
                raise ValueError("_function_name is required in kwargs")

            del kwargs["_function_name"]
            if not hasattr(el, fn):
                raise ValueError(f"{fn} is not a valid function in {el.__name__}")
            if fn == "from_catalog_table":
                if catalog is None:
                    raise ValueError("catalog is required to use `from_catalog_table`, none was provided")
                kwargs["catalog"] = catalog
            el = getattr(el, fn)(
                *pos_args,
                **kwargs,
            )
        return cast(DataFrame, el)

    def to_proto(self) -> "expr_pb.LogicalExprNode":
        """
        Convert this LazyFrame's call stack into a nested LogicalExprNode proto.

        Each entry in the stack becomes an ExprCall, chained via get_attribute on the previous node.
        """

        expr_pb = _require_expr_pb("to_proto")

        # Helper to wrap a Python/pyarrow value into a literal LogicalExprNode
        def _val_to_node(val: Any) -> expr_pb.LogicalExprNode:
            # LazyFrame nested as argument: embed its full proto
            if isinstance(val, LazyFrame):
                return val.to_proto()

            # pyarrow.RecordBatch or Table -> list of struct arrow ScalarValue literal
            if isinstance(val, (_pa.RecordBatch, _pa.Table)):
                rows = val.to_pylist()
                pa_scalar = _pa.scalar(rows)
                pb_scalar = PrimitiveFeatureConverter.from_pyarrow_to_protobuf(pa_scalar)
                lit = expr_pb.ExprLiteral(value=pb_scalar, is_arrow_scalar_object=True)
                return expr_pb.LogicalExprNode(literal_value=lit)

            # assume the keys are strings and the values need to be converted
            if isinstance(val, dict):
                converted_values = {k: _val_to_node(v) for k, v in val.items()}
                return expr_pb.LogicalExprNode(
                    call=expr_pb.ExprCall(
                        func=expr_pb.LogicalExprNode(identifier=expr_pb.Identifier(name="dict")),
                        kwargs=converted_values,
                    )
                )

            if isinstance(val, Expr):
                return expr_pb.LogicalExprNode.FromString(val.to_proto_bytes())

            # Primitive or pyarrow.Scalar -> arrow ScalarValue literal
            try:
                is_arrow = isinstance(val, _pa.Scalar)
                pa_scalar = val if is_arrow else _pa.scalar(val)
                pb_scalar = PrimitiveFeatureConverter.from_pyarrow_to_protobuf(pa_scalar)
                lit = expr_pb.ExprLiteral(value=pb_scalar, is_arrow_scalar_object=is_arrow)
                return expr_pb.LogicalExprNode(literal_value=lit)
            except Exception:
                raise ValueError(f"Cannot convert argument to proto literal: {val!r}")

        node: expr_pb.LogicalExprNode | None = None
        # iterate through recorded calls in order
        for args, kwargs in self.stack:
            fn = kwargs.get("_function_name")
            if fn is None:
                raise ValueError("_function_name missing for LazyFrame stack entry")
            # copy kwargs except internal marker
            kw = {k: v for k, v in kwargs.items() if k != "_function_name"}
            # build argument protos
            args_nodes = [_val_to_node(a) for a in args]
            kwargs_nodes = {k: _val_to_node(v) for k, v in kw.items()}

            # prepare the function expression: method call on previous node or base frame
            parent = node or expr_pb.LogicalExprNode(identifier=expr_pb.Identifier(name="chalk_data_frame"))
            get_attr = expr_pb.ExprGetAttribute(parent=parent, attribute=expr_pb.Identifier(name=fn))
            func_node = expr_pb.LogicalExprNode(get_attribute=get_attr)

            # build this call node
            call_node = expr_pb.ExprCall(func=func_node, args=args_nodes, kwargs=kwargs_nodes)
            node = expr_pb.LogicalExprNode(call=call_node)

        # if no calls, return bare frame identifier
        return node or expr_pb.LogicalExprNode(identifier=expr_pb.Identifier(name="chalk_data_frame"))

    def _to_proto(self):
        return self.to_proto()

    @classmethod
    def from_proto_str(cls: Type[LazyFrame], node_bytes: bytes) -> LazyFrame:
        expr_pb = _require_expr_pb("from_proto_str")
        return cls.from_proto(expr_pb.LogicalExprNode.FromString(node_bytes))

    @classmethod
    def from_proto(cls: Type[LazyFrame], node: "expr_pb.LogicalExprNode") -> LazyFrame:
        """
        Reconstruct a LazyFrame from its LogicalExprNode proto created by to_proto().

        Traverses nested ExprCall/get_attribute to repopulate the call stack.
        """

        expr_pb = _require_expr_pb("from_proto")

        if not isinstance(node, expr_pb.LogicalExprNode):
            raise TypeError(
                "LazyFrame.from_proto expects an instance of "
                "`chalk._gen.chalk.expression.v1.expression_pb2.LogicalExprNode`."
            )

        # Helper to extract Python/pyarrow value from a literal node
        def _node_to_val(n: expr_pb.LogicalExprNode) -> Any:
            if n.HasField("literal_value"):
                lit = n.literal_value
                pa_scalar = PrimitiveFeatureConverter.from_protobuf_to_pyarrow(lit.value)
                return pa_scalar if lit.is_arrow_scalar_object else pa_scalar.as_py()

            # dict literal nodes -> Python dict
            if n.HasField("call") and n.call.func.HasField("identifier") and n.call.func.identifier.name == "dict":
                return {k: _node_to_val(v) for k, v in n.call.kwargs.items()}

            # Expr literal/logical nodes -> libchalk Expr
            try:
                return Expr.from_proto(n)
            except Exception:
                pass

            # nested LazyFrame calls
            if n.HasField("call") or n.HasField("get_attribute"):
                return cls.from_proto(n)

            raise ValueError(f"Unsupported literal node for LazyFrame.from_proto: {n}")

        lf = cls()
        # collect (args, kwargs, fn) entries in reverse order
        calls: list[tuple[tuple[Any, ...], dict[str, Any], str]] = []
        cur = node
        # unwind nested calls
        while True:
            if cur.HasField("call"):
                call = cur.call
                fn = None
                func = call.func
                if func.HasField("get_attribute"):
                    fn = func.get_attribute.attribute.name
                    parent = func.get_attribute.parent
                elif func.HasField("identifier"):
                    name = func.identifier.name
                    if name == "chalk_data_frame":
                        # reached base, stop unwinding
                        break
                    fn = name
                    parent = None
                else:
                    break

                # decode args/kwargs
                args = tuple(_node_to_val(a) for a in call.args)
                kwargs = {k: _node_to_val(v) for k, v in call.kwargs.items()}
                calls.append((args, kwargs, fn))
                # move up to parent for next iteration
                if func.HasField("get_attribute") and parent is not None:
                    cur = parent
                    continue
            break

        # rebuild stack in original order
        for args, kwargs, fn in reversed(calls):
            kwargs = {**kwargs, "_function_name": fn}
            lf.stack.append((args, kwargs))
        return lf

    @classmethod
    def plan_from_proto_str(cls: Type[LazyFrame], node_bytes: bytes, catalog: ChalkSqlCatalog | None) -> ChalkTable:
        expr_pb = _require_expr_pb("plan_from_proto_str")
        return cls.plan_from_proto(expr_pb.LogicalExprNode.FromString(node_bytes), catalog=catalog)

    @classmethod
    def plan_from_proto(
        cls: Type[LazyFrame], node: "expr_pb.LogicalExprNode", catalog: ChalkSqlCatalog | None = None
    ) -> ChalkTable:
        expr_pb = _require_expr_pb("plan_from_proto")
        if not isinstance(node, expr_pb.LogicalExprNode):
            raise TypeError(
                "LazyFrame.from_proto expects an instance of "
                "`chalk._gen.chalk.expression.v1.expression_pb2.LogicalExprNode`."
            )
        lazy_frame = LazyFrame.from_proto(node)
        df = lazy_frame._convert_to_df(catalog=catalog)
        res = df.get_plan()
        return res

    def __repr__(self) -> str:
        if not self.stack:
            return "LazyFrame()"
        lines: list[str] = ["LazyFrame(", "    chalk_data_frame"]
        for args, kwargs in self.stack:
            fn = kwargs.get("_function_name")
            kw = {k: v for k, v in kwargs.items() if k != "_function_name"}
            args_repr = ", ".join(repr(a) for a in args)
            kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in kw.items())
            all_args = ", ".join(x for x in (args_repr, kwargs_repr) if x)
            lines.append(f"    .{fn}({all_args})")
        lines.append(")")
        return "\n".join(lines)

    __str__ = __repr__

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LazyFrame):
            return NotImplemented

        return self.stack == other.stack
