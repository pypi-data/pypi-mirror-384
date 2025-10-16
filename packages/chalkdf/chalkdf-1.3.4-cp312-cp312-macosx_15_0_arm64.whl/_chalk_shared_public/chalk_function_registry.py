from __future__ import annotations

import base64
import collections
import datetime
import decimal
import difflib
import gzip
import hashlib
import math
import operator
import random
import re
import statistics
import typing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping, Optional, TypeVar

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
from chalk.features import Vector
from chalk.features._encoding.http import HttpResponse
from chalk.features._encoding.pyarrow import rich_to_pyarrow
from chalk.prompts import MultimodalPromptResponse, PromptResponse
from chalk.utils.collections import OrderedSet
from chalk.utils.json import TJSON, pyarrow_json_type

from libchalk.chalkfunction import (
    AGGREGATE_FUNCTIONS,
    BASE_FUNCTIONS,
    ArgumentType,
    ChalkFunctionOverload,
    ChalkFunctionOverloadFailed,
    ChalkFunctionOverloadResolved,
    DataFrameParameterType,
    FunctionRegistry,
    default_arrow_type_promoter,
)
from libchalk.chalkfunction import (
    make_generic as generic,
)
from libchalk.udf import (
    BlockingCallChalkFunctionImpl,
    DirectChalkFunctionImpl,
    HttpRequestBlockingFunction,
)

from .arrow_type_promotion import (
    datetime_type,
    duration_type,
    most_precise_numeric_type_from_arrow,
    pa_date_types,
    pa_float_types,
    pa_int_types,
)

if TYPE_CHECKING:
    from libchalk.chalkfunction import MaybeNamedCollection

T = TypeVar("T")
V = TypeVar("V")

T1 = TypeVar("T1")
T2 = TypeVar("T2")


@dataclass
class _NullCheckedOp(Generic[T1, T2, V]):
    op: Callable[[T1, T2], V]

    def __call__(self, x: T1 | None, y: T2 | None) -> V | None:
        return None if x is None or y is None else self.op(x, y)


@dataclass
class _UpcastDatesOp(Generic[T1, T2, V]):
    """
    When called with a mixture of date and datetime, upcasts them both to be datetime.

    The upcasted datetime is explicitly UTC because we assume any other datetimes we
    encounter will also be explicitly UTC.
    """

    op: Callable[[T1, T2], V]

    def __call__(self, x: T1, y: T2) -> V:
        upcast = lambda d: datetime.datetime.combine(d, datetime.time(), tzinfo=datetime.timezone.utc)
        match (x, y):
            case (datetime.datetime(), datetime.date()):
                return self.op(x, upcast(y))
            case (datetime.date(), datetime.datetime()):
                return self.op(upcast(x), y)
            case _:
                return self.op(x, y)


def _coalesce_op(*args: T | None) -> T | None:
    for arg in args:
        if arg is not None:
            return arg
    return None


@dataclass
class _CosineSimilarityOp:
    """
    Cosine similarity between two vectors, represented as tuples of floats.

    The Cosine similarity between two vectors :math:`u` and :math:`v` is defined as:

    .. math::

        \\frac{u \\cdot v}{\\|u\\| \\|v\\|}

    where :math:`u \\cdot v` is the dot product of :math:`u` and :math:`v`, and
    :math:`\\|u\\|` and :math:`\\|v\\|` are the magnitudes of :math:`u` and :math:`v`.
    """

    def __call__(self, A: Vector, B: Vector) -> float:
        u = A.to_numpy()
        v = B.to_numpy()

        uv = np.dot(u, v)
        uu, vv = np.linalg.norm(u), np.linalg.norm(v)
        if uu == 0 or vv == 0:
            return 0
        return uv / (uu * vv)


@dataclass
class _DotProductOp:
    """
    Dot Product between two vectors, represented as tuples of floats.

    """

    def __call__(self, A: Vector, B: Vector) -> float:
        u = A.to_numpy()
        v = B.to_numpy()

        uv = np.dot(u, v)
        return uv


@dataclass
class _ArrayNormalizeOp:
    """
    L_p normalization of a vector, represented as tuples of floats.

    """

    def __call__(self, A: Vector, p: float) -> Vector:
        u = A.to_numpy()
        lp_norm = np.linalg.norm(u, ord=p)
        return Vector(u / lp_norm)


@dataclass
class _SagemakerPredictOp:
    def __call__(
        self,
        body: bytes,
        endpoint: str,
        content_type: str | None,
        target_model: str | None,
        target_variant: str | None,
        aws_access_key_id_override: str | None,
        aws_secret_access_key_override: str | None,
        aws_session_token_override: str | None,
        aws_role_arn_override: str | None,
        aws_region_override: str | None,
        aws_profile_name_override: str | None,
        inference_component: str | None,
    ) -> Any:
        import boto3

        # TODO: Currently problematic because of session creation at runtime. We NEED to construct the sessions
        # at boot or plan time

        # this is a little rough, but explicitly setting boto3 session variables to None and not setting them at all
        # are different, so we need to impl it like this
        if aws_role_arn_override:
            sts_client = boto3.client("sts")
            response = sts_client.assume_role(
                RoleArn=aws_role_arn_override, RoleSessionName="chalk_sagemaker_predict_session"
            )
            aws_access_key_id_override = response["Credentials"]["AccessKeyId"]
            aws_secret_access_key_override = response["Credentials"]["SecretAccessKey"]
            aws_session_token_override = response["Credentials"]["SessionToken"]

        boto_session_kwargs = {}

        if aws_access_key_id_override is not None:
            boto_session_kwargs["aws_access_key_id"] = aws_access_key_id_override
        if aws_secret_access_key_override is not None:
            boto_session_kwargs["aws_secret_access_key"] = aws_secret_access_key_override
        if aws_session_token_override is not None:
            boto_session_kwargs["aws_session_token"] = aws_session_token_override
        if aws_region_override is not None:
            boto_session_kwargs["region_name"] = aws_region_override
        if aws_profile_name_override is not None:
            boto_session_kwargs["profile_name"] = aws_profile_name_override

        boto_session = boto3.Session(**boto_session_kwargs)
        sagemaker_client = boto_session.client("sagemaker-runtime")

        invoke_endpoint_kwargs = {}
        # Same thing as above: passing in None is not the same as not passing in anything
        if content_type is not None:
            invoke_endpoint_kwargs["ContentType"] = content_type
        if target_model is not None:
            invoke_endpoint_kwargs["TargetModel"] = target_model
        if target_variant is not None:
            invoke_endpoint_kwargs["TargetVariant"] = target_variant
        if inference_component is not None:
            invoke_endpoint_kwargs["InferenceComponentName"] = inference_component

        resp_dict = sagemaker_client.invoke_endpoint(EndpointName=endpoint, Body=body, **invoke_endpoint_kwargs)
        return resp_dict["Body"].read()


VELOX_ZIP_ARITIES = tuple(range(2, 8))

PA_LIST_TYPES = (pa.list_, pa.large_list)
PA_LARGEST_NUM_TYPES = (pa.int64(), pa.float64())

PA_STRING_TYPES = (pa.string(), pa.large_string())
PA_BINARY_TYPES = (pa.binary(), pa.large_binary())
PA_INT_TYPES = tuple(pa_int_types.values())
PA_FLOAT_TYPES = tuple(pa_float_types.values())
PA_NUM_TYPES = PA_INT_TYPES + PA_FLOAT_TYPES
PA_TIMESTAMP_TYPES = (datetime_type,)
PA_DURATION_TYPES = (duration_type,)
PA_DATE_TYPES = tuple(pa_date_types.values())

PA_NUM_AND_TIME_TYPES = PA_NUM_TYPES + PA_TIMESTAMP_TYPES + PA_DURATION_TYPES + PA_DATE_TYPES
PA_BUILTIN_SCALAR_TYPES = (
    PA_NUM_TYPES + PA_STRING_TYPES + PA_BINARY_TYPES + PA_TIMESTAMP_TYPES + PA_DURATION_TYPES + PA_DATE_TYPES
)


# Functions that depend on pyarrow_json_type().
JSON_FUNCTIONS = FunctionRegistry(
    default_arrow_type_promoter,
    {
        "eq": [
            ChalkFunctionOverload(
                function_name="eq",
                description="Compares if two values are equal.",
                overload_generic_parameters=[pyarrow_json_type(), pyarrow_json_type()],
                overload_generic_return=pa.bool_(),
                pybind_function="eq",
            )
        ],
        "neq": [
            ChalkFunctionOverload(
                function_name="neq",
                description="Compares if two values are not equal.",
                overload_generic_parameters=[pyarrow_json_type(), pyarrow_json_type()],
                overload_generic_return=pa.bool_(),
                pybind_function="neq",
            )
        ],
        "get_json_value": [
            ChalkFunctionOverload(
                function_name="json_extract",
                description="Extracts a value from JSON using a path expression.",
                overload_generic_parameters=[pyarrow_json_type(), pa.large_string()],
                overload_generic_return=pyarrow_json_type(),
                pybind_function="json_extract",
            ),
            ChalkFunctionOverload(
                function_name="json_extract",
                description="Extracts a value from JSON string using a path expression.",
                overload_generic_parameters=[pa.large_string(), pa.large_string()],
                overload_generic_return=pyarrow_json_type(),
                pybind_function="json_extract",
            ),
        ],
        "json_extract_array": [
            ChalkFunctionOverload(
                function_name="json_extract_array",
                description="Extracts an array from JSON string using a path expression.",
                overload_generic_parameters=[pa.large_string(), pa.large_string()],
                overload_generic_return=pa.large_list(pyarrow_json_type()),
                pybind_function="json_extract_array",
            ),
            ChalkFunctionOverload(
                function_name="json_extract_array",
                description="Extracts an array from JSON string using a path expression.",
                overload_generic_parameters=[pyarrow_json_type(), pa.large_string()],
                overload_generic_return=pa.large_list(pyarrow_json_type()),
                pybind_function="json_extract_array",
            ),
        ],
    },
)

MultimodalContentItem = Mapping[str, str | None]
MultimodalMessageContents = list[MultimodalContentItem]


def _transform_content(content: MultimodalContentItem) -> Mapping[str, Any]:
    content_type = content.get("type")
    if content_type == "text" or content_type == "input_text":
        return {"type": "text", "text": content["text"]}
    elif content_type == "image_url" or content_type == "input_image":
        image_url_obj = {"url": content["image_url"]}
        if content.get("detail") is not None:
            image_url_obj["detail"] = content["detail"]
        return {"type": "image_url", "image_url": image_url_obj}
    else:
        raise ValueError(f"Unknown content type: {content_type}")


def _transform_messages(
    messages: list[Mapping[str, MultimodalMessageContents]],
) -> list[Mapping[str, list[Mapping[str, Any]]]]:
    return [
        {
            "role": message["role"],
            "content": [_transform_content(content) for content in message["content"]],
        }
        for message in messages
    ]


def _is_multimodal_messages(messages: list[Mapping[str, str | MultimodalMessageContents]]) -> bool:
    if not messages:
        return False
    return isinstance(messages[0].get("content"), list)


def _sanitize_contents(contents: MultimodalMessageContents) -> list[Mapping[str, str]]:
    return [{k: v for k, v in content.items() if v is not None} for content in contents]


def _convert_pydantic_to_langchain(
    schema: dict[str, TJSON],
) -> TJSON:
    # reimplementation of langchain's convert_pydantic_to_openai_function so that it accepts a dict
    # rather than the pydantic basemodel class
    schema.pop("definitions", None)
    name = schema.pop("title", "")
    description = schema.pop("description", "")
    return {
        "name": name,
        "description": description,
        "parameters": schema,
    }


@dataclass
class UsageCounter:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, input_tokens: int, output_tokens: int, total_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens


def _completion_op(
    model: str,
    messages: list[Mapping[str, str | MultimodalMessageContents]],
    timeout_seconds: float | None,
    output_structure: str | None,
    temperature: Optional[float],
    top_p: Optional[float],
    max_completion_tokens: Optional[int],
    max_tokens: Optional[int],
    stop: Optional[list[str]],
    presence_penalty: Optional[float],
    frequency_penalty: Optional[float],
    logit_bias: Optional[dict[int, float]],
    seed: Optional[int],
    user: Optional[str],
    model_provider: Optional[str],
    base_url: Optional[str],
    api_key: Optional[str],
    num_retries: Optional[int],
) -> Any:
    import json

    from chalk.prompts import (
        Message,
        MultimodalMessage,
        MultimodalPrompt,
        MultimodalPromptResponse,
        Prompt,
        PromptResponse,
        RuntimeStats,
        Usage,
    )
    from chalk.utils.tracing import PerfTimer
    from langchain.chat_models import init_chat_model
    from tenacity import (
        RetryError,
        Retrying,
        retry_if_exception_message,
        retry_if_not_exception_message,
        retry_if_not_exception_type,
        stop_after_attempt,
        stop_after_delay,
        wait_exponential_jitter,
    )

    with PerfTimer() as overall_pt:
        is_multimodal_prompt = _is_multimodal_messages(messages)
        if is_multimodal_prompt:
            # guaranteed by _is_multimodal_messages check
            multimodal_messages = typing.cast(list[Mapping[str, MultimodalMessageContents]], messages)
            transformed_messages = _transform_messages(multimodal_messages)
        else:
            transformed_messages = messages

        # pyright does not understand langchain
        model_obj = init_chat_model(  # pyright: ignore[reportCallIssue]
            model=model,
            timeout=timeout_seconds,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
            max_tokens=max_tokens,
            stop=stop,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            seed=seed,
            model_provider=model_provider,
            base_url=base_url,
            api_key=api_key,
            max_retries=0,  # custom retry logic below
            user=user,  # pyright: ignore[reportArgumentType]
            **({"temperature": temperature} if temperature is not None else {}),  # pyright: ignore[reportArgumentType]
        )
        if output_structure is not None:
            try:
                output_structure_langchain = _convert_pydantic_to_langchain(json.loads(output_structure))
                model_obj = model_obj.with_structured_output(output_structure_langchain, include_raw=True)
            except Exception as e:
                raise ValueError(
                    f"Prompt requested output structure `{output_structure}`, which is not a valid JSON representation of a Pydantic model."
                    + "Use Model.model_json_schema() (Pydantic V2) or Model.schema_json() (Pydantic V1) to get the JSON representatino of a model."
                    + f"Error details: {e}"
                )

        response = None
        raw: Any = None
        total_tries = 0
        general_tries = 0
        last_try_latency: float | None = None
        usage_counter = UsageCounter()

        general_stop = stop_after_attempt(1 if num_retries is None else num_retries + 1)
        if timeout_seconds is not None:
            general_stop |= stop_after_delay(timeout_seconds)
        for general_attempt in Retrying(
            retry=retry_if_not_exception_type(RetryError) & retry_if_not_exception_message(match=r".*429.*"),
            wait=wait_exponential_jitter(),
            stop=general_stop,
            reraise=True,
        ):
            general_tries += 1
            with general_attempt:
                output: Any = None
                stop_429 = stop_after_attempt(10)
                if timeout_seconds is not None:
                    stop_429 |= stop_after_delay(timeout_seconds)
                for attempt_429 in Retrying(
                    retry=retry_if_exception_message(match=r".*429.*"),
                    wait=wait_exponential_jitter(),
                    stop=stop_429,
                    reraise=True,
                ):
                    total_tries += 1
                    with attempt_429:
                        with PerfTimer() as last_try_pt:
                            output = model_obj.invoke(transformed_messages)
                        last_try_latency = last_try_pt.duration_seconds

                if output_structure is not None:
                    raw = output["raw"]
                else:
                    raw = output
                usage_counter.add(
                    input_tokens=raw.usage_metadata["input_tokens"],
                    output_tokens=raw.usage_metadata["output_tokens"],
                    total_tokens=raw.usage_metadata["total_tokens"],
                )
                if output_structure is not None:
                    if output["parsing_error"] is not None:
                        raise ValueError(output["parsing_error"])
                    response = json.dumps(output["parsed"]) if output["parsed"] is not None else None
                else:
                    response = output.content

    usage = Usage(
        input_tokens=usage_counter.input_tokens,
        output_tokens=usage_counter.output_tokens,
        total_tokens=usage_counter.total_tokens,
    )
    runtime_stats = RuntimeStats(
        total_latency=overall_pt.duration_seconds,
        last_try_latency=last_try_latency,
        total_retries=total_tries - 1,
        rate_limit_retries=total_tries - general_tries,
    )
    if is_multimodal_prompt:
        return MultimodalPromptResponse(
            response=response,
            prompt=MultimodalPrompt(
                model=model,
                messages=[
                    MultimodalMessage(
                        role=typing.cast(str, message["role"]),
                        content=_sanitize_contents(typing.cast(MultimodalMessageContents, message["content"])),
                    )
                    for message in messages
                ],
                output_structure=output_structure,
                timeout_seconds=timeout_seconds,
                temperature=temperature,
                top_p=top_p,
                max_completion_tokens=max_completion_tokens,
                max_tokens=max_tokens,
                stop=stop,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                seed=seed,
                user=user,
                model_provider=model_provider,
                base_url=base_url,
                num_retries=num_retries,
            ),
            usage=usage,
            runtime_stats=runtime_stats,
        ).dict()
    else:
        return PromptResponse(
            response=response,
            prompt=Prompt(
                model=model,
                messages=[
                    Message(
                        role=typing.cast(str, message["role"]),
                        content=typing.cast(str, message["content"]),
                    )
                    for message in messages
                ],
                output_structure=output_structure,
                timeout_seconds=timeout_seconds,
                temperature=temperature,
                top_p=top_p,
                max_completion_tokens=max_completion_tokens,
                max_tokens=max_tokens,
                stop=stop,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                seed=seed,
                user=user,
                model_provider=model_provider,
                base_url=base_url,
                num_retries=num_retries,
            ),
            usage=usage,
            runtime_stats=runtime_stats,
        ).dict()


def _jinja_op(template: str, context: dict[str, Any]) -> str:
    try:
        import jinja2

        return jinja2.Environment().from_string(template).render(context)
    except:
        return ""


LLM_FUNCTIONS = FunctionRegistry(
    default_arrow_type_promoter,
    {
        "completion": [
            ChalkFunctionOverload(
                function_name="completion",
                description="Generates text completions using a language model with string-based message content.",
                overload_generic_parameters=[],
                overload_generic_named_parameters=[
                    ("model", pa.large_string()),
                    (
                        "messages",
                        pa.large_list(
                            pa.struct(
                                {
                                    "role": pa.large_string(),
                                    "content": pa.large_string(),
                                }
                            )
                        ),
                    ),
                    ("timeout_seconds", pa.float64()),
                    ("output_structure", pa.large_string()),
                    ("temperature", pa.float64()),
                    ("top_p", pa.float64()),
                    ("max_completion_tokens", pa.int64()),
                    ("max_tokens", pa.int64()),
                    ("stop", pa.large_list(pa.large_string())),
                    ("presence_penalty", pa.float64()),
                    ("frequency_penalty", pa.float64()),
                    ("logit_bias", pa.map_(pa.int64(), pa.float64())),
                    ("seed", pa.int64()),
                    ("user", pa.large_string()),
                    ("model_provider", pa.large_string()),
                    ("base_url", pa.large_string()),
                    ("api_key", pa.large_string()),
                    ("num_retries", pa.int64()),
                ],
                overload_generic_return=rich_to_pyarrow(PromptResponse, name="PromptResponse"),
                pybind_function=None,
                python_fallback=_completion_op,
            ),
            ChalkFunctionOverload(
                function_name="completion",
                description="Generates text completions using a language model with multimodal message content (text and images).",
                overload_generic_parameters=[],
                overload_generic_named_parameters=[
                    ("model", pa.large_string()),
                    (
                        "messages",
                        pa.large_list(
                            pa.struct(
                                {
                                    "role": pa.large_string(),
                                    "content": pa.large_list(
                                        pa.struct(
                                            {
                                                "type": pa.large_string(),
                                                "text": pa.large_string(),
                                                "image_url": pa.large_string(),
                                                "detail": pa.large_string(),
                                            }
                                        )
                                    ),
                                }
                            )
                        ),
                    ),
                    ("timeout_seconds", pa.float64()),
                    ("output_structure", pa.large_string()),
                    ("temperature", pa.float64()),
                    ("top_p", pa.float64()),
                    ("max_completion_tokens", pa.int64()),
                    ("max_tokens", pa.int64()),
                    ("stop", pa.large_list(pa.large_string())),
                    ("presence_penalty", pa.float64()),
                    ("frequency_penalty", pa.float64()),
                    ("logit_bias", pa.map_(pa.int64(), pa.float64())),
                    ("seed", pa.int64()),
                    ("user", pa.large_string()),
                    ("model_provider", pa.large_string()),
                    ("base_url", pa.large_string()),
                    ("api_key", pa.large_string()),
                    ("num_retries", pa.int64()),
                ],
                overload_generic_return=rich_to_pyarrow(MultimodalPromptResponse, name="MultimodalPromptResponse"),
                pybind_function=None,
                python_fallback=_completion_op,
            ),
        ],
        "jinja": [
            ChalkFunctionOverload(
                function_name="jinja",
                description="Renders a Jinja2 template string with provided context variables.",
                overload_generic_parameters=[pa.large_string(), generic("T")],
                overload_generic_return=pa.large_string(),
                pybind_function=None,
                python_fallback=_jinja_op,
            )
        ],
        "run_prompt": [
            ChalkFunctionOverload(
                function_name="run_prompt",
                description="Executes a named prompt template and returns the generated response.",
                overload_generic_parameters=[],
                overload_generic_named_parameters=[
                    ("prompt_name", pa.large_string()),
                ],
                overload_generic_return=rich_to_pyarrow(PromptResponse, name="PromptResponse"),
                pybind_function=None,
                python_fallback=None,
            ),
            ChalkFunctionOverload(
                function_name="run_prompt",
                description="Executes a prompt template by its ID and returns the response.",
                overload_generic_parameters=[],
                overload_generic_named_parameters=[
                    ("propmt_id", pa.int64()),
                ],
                overload_generic_return=rich_to_pyarrow(PromptResponse, name="PromptResponse"),
                pybind_function=None,
                python_fallback=None,
            ),
        ],
    },
)
UDF_BASED_FUNCTIONS = FunctionRegistry(
    default_arrow_type_promoter,
    {
        "http_request": [
            # ChalkFunctionOverload(
            #     function_name="http_request",
            #     overload_generic_parameters=[
            #         pa.large_string(),
            #         pa.large_string(),
            #         pa.map_(pa.large_string(), pa.large_string()),
            #         pa.large_string(),
            #         pa.bool_(),
            #         pa.int64(),
            #     ],
            #     overload_generic_return=rich_to_pyarrow(HttpResponse[str], name="HttpResponse[str]"),
            #     pybind_function=make_http_udf_chalk_function(),
            #     python_fallback=None,
            # ),
            # ChalkFunctionOverload(
            #     function_name="http_request",
            #     overload_generic_parameters=[
            #         pa.large_string(),
            #         pa.large_string(),
            #         pa.map_(pa.large_string(), pa.large_string()),
            #         pa.large_binary(),
            #         pa.bool_(),
            #         pa.int64(),
            #     ],
            #     overload_generic_return=rich_to_pyarrow(HttpResponse[str], name="HttpResponse[str]"),
            #     pybind_function=make_http_udf_chalk_function(),
            #     python_fallback=None,
            # ),
            ChalkFunctionOverload(
                function_name="http_request",
                description="Makes an HTTP request with string body and returns the response as bytes.",
                overload_generic_parameters=[
                    pa.large_string(),
                    pa.large_string(),
                    pa.map_(pa.large_string(), pa.large_string()),
                    pa.large_string(),
                    pa.bool_(),
                    pa.int64(),
                ],
                overload_generic_return=rich_to_pyarrow(HttpResponse[bytes], name="HttpResponse[bytes]"),
                pybind_function=BlockingCallChalkFunctionImpl(HttpRequestBlockingFunction()),
                python_fallback=None,
            ),
            ChalkFunctionOverload(
                function_name="http_request",
                description="Makes an HTTP request with binary body and returns the response as bytes.",
                overload_generic_parameters=[
                    pa.large_string(),
                    pa.large_string(),
                    pa.map_(pa.large_string(), pa.large_string()),
                    pa.large_binary(),
                    pa.bool_(),
                    pa.int64(),
                ],
                overload_generic_return=rich_to_pyarrow(HttpResponse[bytes], name="HttpResponse[bytes]"),
                pybind_function=BlockingCallChalkFunctionImpl(HttpRequestBlockingFunction()),
                python_fallback=None,
            ),
        ],
        "onnx_run_embedding": [
            ChalkFunctionOverload(
                function_name="onnx_run_embedding",
                description="Generates embeddings from text using the specified ONNX model.",
                overload_generic_parameters=[
                    pa.large_string(),
                ],
                overload_generic_return=pa.large_list(pa.float32()),
                overload_generic_named_parameters=[
                    ("model_name", pa.large_string()),
                ],
                pybind_function="onnx_run_embedding",
                python_fallback=None,
            ),
        ],
        "sagemaker_predict": [
            ChalkFunctionOverload(
                function_name="sagemaker_predict",
                description="Invokes an AWS SageMaker endpoint for inference with the provided binary input and returns the binary output.",
                overload_generic_parameters=[bin_type],
                overload_generic_named_parameters=[
                    ("endpoint", str_type),
                    ("content_type", str_type),
                    ("target_model", str_type),
                    ("target_variant", str_type),
                    ("aws_access_key_id_override", str_type),
                    ("aws_secret_access_key_override", str_type),
                    ("aws_session_token_override", str_type),
                    ("aws_role_arn_override", str_type),
                    ("aws_region_override", str_type),
                    ("aws_profile_name_override", str_type),
                    ("inference_component", str_type),
                ],
                overload_generic_return=bin_type,
                pybind_function="sagemaker_predict",
                python_fallback=_SagemakerPredictOp(),
            )
            for bin_type, str_type in zip(PA_BINARY_TYPES, PA_STRING_TYPES)
        ],
    },
)


def _velox_only_agg(fn_name: str):
    def _inner(*args: Any):
        raise NotImplementedError(f"aggregate function {fn_name} is only supported on Velox")

    return _inner


def _exact_count_distinct_fn_from_func_name(func_name: str):
    def _exact_count_distinct_fn(input: Any):
        if not isinstance(input, (pa.Array, pa.ChunkedArray)):
            raise ValueError(f"Cannot run `.{func_name}()` on non-array input of type '{type(input)}'")

        return pc.count_distinct(input).as_py()

    return _exact_count_distinct_fn


def _approx_percentile_fn(input: Any, quantile: float):
    if not isinstance(input, (pa.Array, pa.ChunkedArray)):
        raise ValueError(f"Cannot run `.approx_percentile()` on non-array input of type '{type(input)}'")

    try:
        quantile = float(quantile)
    except:
        raise TypeError(
            f"The quantile value must be float in the range [0, 1], but got {repr(quantile)} with type '{type(quantile)}'"
        )

    if not (0 <= quantile <= 1):
        raise ValueError(
            f"Cannot run `.approx_percentile()` with quantile value '{repr(quantile)}' outside of the legal range [0, 1]"
        )

    return pc.quantile(input, q=quantile)[0].as_py()


def _replace_python_fallback(
    overload: ChalkFunctionOverload, python_fallback: Callable[..., Any] | None
) -> ChalkFunctionOverload:
    return ChalkFunctionOverload(
        # Most fields stay the same.
        function_name=overload.function_name,
        description=overload.description,
        overload_generic_parameters=overload.overload_generic_parameters,
        overload_generic_return=overload.overload_generic_return,
        overload_generic_named_parameters=overload.overload_generic_named_parameters,
        overload_force_cast_parameters=overload.overload_force_cast_parameters,
        overload_force_cast_output_from_velox_type=overload.overload_force_cast_output_from_velox_type,
        pybind_function=overload.pybind_function,
        pybind_method_pack_arguments=overload.pybind_method_pack_arguments,
        convert_input_errors_to_none=overload.convert_input_errors_to_none,
        # python_fallback gets replaced.
        python_fallback=python_fallback,
    )


def remove_python_fallbacks(registry: FunctionRegistry) -> FunctionRegistry:
    result = FunctionRegistry(registry.type_promoter)

    for name in registry.all_names():
        for overload in registry.lookup_overloads(name):
            result.add(name, _replace_python_fallback(overload, None))

    return result


@dataclass
class _OverloadPattern:
    """Identifies one or more overloads in a function registry."""

    name: str | None = None
    """Matches the name that the overload is bound to, in the registry."""

    function_name: str | None = None
    """Matches the overload's function_name property."""

    arity: int | None = None
    """Matches overloads that have exactly N and only this many positional arguments."""

    return_type: pa.DataType | None = None
    """Matches overloads that have this exact return type."""

    def matches(self, name: str, overload: ChalkFunctionOverload):
        if self.name and self.name != name:
            return False

        if self.function_name and self.function_name != overload.function_name:
            return False

        if self.arity:
            if overload.variadic_parameter:
                return False
            if overload.overload_generic_named_parameters:
                return False
            if len(overload.overload_generic_parameters) != self.arity:
                return False

        if self.return_type and overload.overload_generic_return != self.return_type:
            return False

        return True


def add_python_fallbacks(
    registry: FunctionRegistry,
    replacements: list[tuple[_OverloadPattern, Callable[..., Any]]],
) -> FunctionRegistry:
    all_overloads = [
        (name, overload)
        for name in registry.all_names()
        for overload in registry.lookup_overloads(name)
        #
    ]

    # Maps from a position in 'all_overloads' to a position in 'replacements',
    # if that replacement's pattern matched this overload.
    overload_replacement_indices: list[int | None] = [None for _ in all_overloads]

    for overload_ix, (name, overload) in enumerate(all_overloads):
        for pattern_ix, (pattern, _) in enumerate(replacements):
            if pattern.matches(name, overload):
                other_pattern_ix = overload_replacement_indices[overload_ix]
                if other_pattern_ix is None:
                    overload_replacement_indices[overload_ix] = pattern_ix
                else:
                    raise ValueError(
                        f"Patterns overlapped: {pattern} and {replacements[other_pattern_ix][0]} both matched {repr(name)}: {overload}"
                    )

    # Make sure every rule matched at least once.
    unmatched_indices = set(range(len(replacements))) - set(overload_replacement_indices)
    if unmatched_indices:
        ix = sorted(list(unmatched_indices))[0]
        raise ValueError(f"Pattern did not match anything: {replacements[ix][0]}")

    # Build a new registry with replacements applied.
    result = FunctionRegistry(registry.type_promoter)
    for ix, (name, overload) in zip(overload_replacement_indices, all_overloads):
        if ix is not None:
            overload = _replace_python_fallback(overload, replacements[ix][1])
        result.add(name, overload)
    return result


_AGGREGATE_FUNCTION_OVERLOADS = {
    "sum": [
        *(
            ChalkFunctionOverload(
                function_name="sum",
                description="Returns the sum of a df column",
                overload_generic_parameters=[DataFrameParameterType(columns={"series": num_type})],
                overload_generic_return=num_type,
                pybind_function="sum",
            )
            for num_type in PA_NUM_TYPES
        ),
        *(
            ChalkFunctionOverload(
                function_name="vector_sum",
                description="Returns the vectorized sum of a df column",
                overload_generic_parameters=[DataFrameParameterType(columns={"series": list_type(num_type)})],
                overload_generic_return=list_type(num_type),
                pybind_function="vector_sum",
            )
            for num_type in PA_NUM_TYPES
            for list_type in PA_LIST_TYPES
        ),
    ],
    "min": [
        ChalkFunctionOverload(
            function_name="min",
            description="Returns the min value of a df column",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": num_type})],
            overload_generic_return=num_type,
            pybind_function="min",
        )
        for num_type in PA_NUM_AND_TIME_TYPES
    ],
    "max": [
        ChalkFunctionOverload(
            function_name="max",
            description="Returns the max value of a df column",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": sortable_type})],
            overload_generic_return=sortable_type,
            pybind_function="max",
        )
        for sortable_type in PA_NUM_AND_TIME_TYPES
    ],
    "mean": [
        *(
            ChalkFunctionOverload(
                function_name="mean",
                description="Returns the mean value of a df column",
                overload_generic_parameters=[DataFrameParameterType(columns={"series": num_type})],
                overload_generic_return=most_precise_numeric_type_from_arrow(
                    types=[num_type], minimum_type=pa.float16()
                ),
                pybind_function="mean",
            )
            for num_type in PA_NUM_TYPES
        ),
        *(
            ChalkFunctionOverload(
                function_name="vector_mean",
                description="Returns the vectorized mean of a df column",
                overload_generic_parameters=[DataFrameParameterType(columns={"series": list_type(num_type)})],
                overload_generic_return=list_type(num_type),
                pybind_function="vector_mean",
            )
            for num_type in PA_NUM_TYPES
            for list_type in PA_LIST_TYPES
        ),
    ],
    "mode": [
        ChalkFunctionOverload(
            function_name="mode",
            description="Returns the mode value of a df column",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": num_type})],
            overload_generic_return=num_type,
            pybind_function="mode",
        )
        for num_type in PA_NUM_TYPES
    ],
    "count": [
        ChalkFunctionOverload(
            function_name="count_all",
            description="Returns the number of entries in a df",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": generic("T")})],
            overload_generic_return=pa.int64(),
            pybind_function="count_all",
        )
    ],
    "any": [
        ChalkFunctionOverload(
            function_name="any",
            description="Returns True if any of the entries in a df column are True",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": pa.bool_()})],
            overload_generic_return=pa.bool_(),
            pybind_function="any",
        )
    ],
    "all": [
        ChalkFunctionOverload(
            function_name="all",
            description="Returns True if all of the entries in a df column are True",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": pa.bool_()})],
            overload_generic_return=pa.bool_(),
            pybind_function="all",
        )
    ],
    **{
        stddev_alias: [
            ChalkFunctionOverload(
                function_name="stddev_sample",
                description="Returns the sample standard deviation of a df column",
                overload_generic_parameters=[DataFrameParameterType(columns={"series": num_type})],
                overload_generic_return=pa.float64(),
                pybind_function="stddev_sample",
            )
            for num_type in PA_NUM_TYPES
        ]
        for stddev_alias in ("std", "stddev", "std_sample", "stddev_sample")
    },
    **{
        var_alias: [
            ChalkFunctionOverload(
                function_name="variance_sample",
                description="Returns the sample variance of a df column",
                overload_generic_parameters=[DataFrameParameterType(columns={"series": num_type})],
                overload_generic_return=pa.float64(),
                pybind_function="variance_sample",
            )
            for num_type in PA_NUM_TYPES
        ]
        for var_alias in ("var", "var_sample")
    },
    "approx_count_distinct": [
        ChalkFunctionOverload(
            function_name="approx_count_distinct",
            description="Returns an approximate number of distinct entries in a df column",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": generic("T")})],
            overload_generic_return=pa.int64(),
            pybind_function="approx_count_distinct",
        )
    ],
    "max_by": [
        ChalkFunctionOverload(
            function_name="max_by",
            description="Return the maximum value of a df column, sorted by the sort column.",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": generic("V")}), generic("S")],
            overload_generic_return=generic("V"),
            pybind_function="max_by",
        )
    ],
    "max_by_n": [
        ChalkFunctionOverload(
            function_name="max_by_n",
            description="Return the maximum n values of a df column, sorted by the sort column.",
            overload_generic_parameters=[
                DataFrameParameterType(columns={"series": generic("V")}),
                generic("S"),
                pa.int64(),
            ],
            overload_generic_return=list_type(generic("V")),
            pybind_function="max_by_n",
        )
        for list_type in PA_LIST_TYPES
    ],
    "min_by": [
        ChalkFunctionOverload(
            function_name="min_by",
            description="Return the minimum value of a df column, sorted by the sort column.",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": generic("V")}), generic("S")],
            overload_generic_return=generic("V"),
            pybind_function="min_by",
        )
    ],
    "min_by_n": [
        ChalkFunctionOverload(
            function_name="min_by_n",
            description="Return the minimum n values of a df column, sorted by the sort column.",
            overload_generic_parameters=[
                DataFrameParameterType(columns={"series": generic("V")}),
                generic("S"),
                pa.int64(),
            ],
            overload_generic_return=list_type(generic("V")),
            pybind_function="min_by_n",
        )
        for list_type in PA_LIST_TYPES
    ],
    "count_distinct": [
        ChalkFunctionOverload(
            function_name="count_distinct",
            description="Returns the number of distinct entries in a df column",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": generic("T")})],
            overload_generic_return=pa.int64(),
            pybind_function="count_distinct",
        )
    ],
    "array_agg": [
        ChalkFunctionOverload(
            function_name="array_agg",
            description="Returns a scalar array of a df column",
            overload_generic_parameters=[DataFrameParameterType(columns={"series": generic("T")})],
            overload_generic_return=list_type(generic("T")),
            pybind_function="array_agg",
        )
        for list_type in PA_LIST_TYPES
    ],
    "approx_percentile": [
        ChalkFunctionOverload(
            function_name="approx_percentile",
            description="Returns the approximate percentile value of the df column",
            overload_generic_parameters=[
                DataFrameParameterType(columns={"series": num_type})
            ],  # FIXME - Dominic - this agg actually takes in another parameter, "quartile", that's handled differently from all other aggregations
            overload_generic_return=pa.float64(),
            pybind_function="approx_percentile",
        )
        for num_type in PA_NUM_TYPES
    ],
    "approx_top_k": [
        ChalkFunctionOverload(
            function_name="approx_top_k",
            description="Returns the approximate k-most frequent values of the df column",
            overload_generic_parameters=[
                DataFrameParameterType(columns={"series": generic("T")}),
            ],  # FIXME - Dominic - this agg actually takes in other parameters, "k" and "output_type", that are handled differently from all other aggregations
            overload_generic_return=pa.large_list(generic("T")),
            pybind_function="approx_top_k",
        )
    ],
}

# TODO: This probably belongs on the resolved overload. But, why is it keyed differently? e.g. count_all is not registered
# under that name.
AGGREGATE_FUNCTION_NULL_FILLING_DETAILS: Mapping[str, int | None | bool] = {
    # TODO: Looks like these functions all ignore null values? They replace null with an identity element.
    **{fn_name: 0 for fn_name in ("sum", "count_all", "approx_count_distinct", "count_distinct")},
    **{fn_name: False for fn_name in ("any",)},
    **{fn_name: True for fn_name in ("all",)},
    **{
        fn_name: None
        for fn_name in (
            "vector_sum",
            "vector_mean",
            "min",
            "max",
            "mean",
            "mode",
            "stddev_sample",
            "variance_sample",
            "array_agg",
            "approx_percentile",
            "approx_top_k",
            "min_by_n",
            "max_by_n",
            "min_by",
            "max_by",
        )
    },
}

assert all(
    overload.function_name in AGGREGATE_FUNCTION_NULL_FILLING_DETAILS
    for name in AGGREGATE_FUNCTIONS.all_names()
    for overload in AGGREGATE_FUNCTIONS.lookup_overloads(name)
)

# The function registry without python_fallback and without Python-only functions.
_CHALK_FUNCTION_REGISTRY_NO_PYTHON: FunctionRegistry = BASE_FUNCTIONS | AGGREGATE_FUNCTIONS

# The function registry with LLM / UDF extensions and with python_fallbacks.
CHALK_FUNCTION_REGISTRY = add_python_fallbacks(
    _CHALK_FUNCTION_REGISTRY_NO_PYTHON.ordered_union(JSON_FUNCTIONS) | LLM_FUNCTIONS | UDF_BASED_FUNCTIONS,
    [
        (_OverloadPattern(function_name="-"), _NullCheckedOp(operator.sub)),
        (_OverloadPattern(function_name="!="), _UpcastDatesOp(_NullCheckedOp(operator.ne))),
        (_OverloadPattern(function_name="*"), _NullCheckedOp(operator.mul)),
        (_OverloadPattern(function_name="**"), _NullCheckedOp(operator.pow)),
        (_OverloadPattern(function_name="/"), _NullCheckedOp(operator.truediv)),
        (_OverloadPattern(function_name="&"), _NullCheckedOp(operator.and_)),
        (_OverloadPattern(function_name="%"), lambda a, b: (a % b)),
        (_OverloadPattern(function_name="+"), _NullCheckedOp(operator.add)),
        (_OverloadPattern(function_name="<"), _UpcastDatesOp(_NullCheckedOp(operator.lt))),
        (_OverloadPattern(function_name="<="), _UpcastDatesOp(_NullCheckedOp(operator.le))),
        (_OverloadPattern(function_name="=="), _UpcastDatesOp(_NullCheckedOp(operator.eq))),
        (_OverloadPattern(function_name=">"), _UpcastDatesOp(_NullCheckedOp(operator.gt))),
        (_OverloadPattern(function_name=">="), _UpcastDatesOp(_NullCheckedOp(operator.ge))),
        (_OverloadPattern(function_name="|"), _NullCheckedOp(operator.or_)),
        (_OverloadPattern(function_name="abs"), abs),
        (_OverloadPattern(function_name="acos"), math.acos),
        (_OverloadPattern(function_name="all"), lambda x: all(x)),
        (_OverloadPattern(function_name="any"), lambda x: any(x)),
        (
            _OverloadPattern(function_name="approx_count_distinct"),
            _exact_count_distinct_fn_from_func_name("approx_count_distinct"),
        ),
        (_OverloadPattern(function_name="approx_percentile"), _approx_percentile_fn),
        (
            _OverloadPattern(function_name="array_average"),
            lambda arr: ((sum(arr) / len(arr)) if (len(arr) > 0) else None),
        ),
        (_OverloadPattern(function_name="array_constructor"), lambda *args: list(args)),
        (
            _OverloadPattern(function_name="array_cum_sum"),
            lambda arr: [sum(arr[: (i + 1)]) for i in range(len(arr))],
        ),
        (_OverloadPattern(function_name="array_distinct"), lambda arr: list(OrderedSet(arr))),
        (_OverloadPattern(function_name="array_duplicates"), lambda arr: [x for x in arr if (arr.count(x) > 1)]),
        (
            _OverloadPattern(function_name="array_except"),
            lambda arr1, arr2: [x for x in arr1 if (x not in arr2)],
        ),
        (_OverloadPattern(function_name="array_filter"), lambda *args: None),
        (_OverloadPattern(function_name="array_frequency"), lambda m: dict(collections.Counter(m))),
        (_OverloadPattern(function_name="array_has_duplicates"), lambda arr: (len(arr) != len(set(arr)))),
        (_OverloadPattern(function_name="array_intersect"), lambda arr1, arr2: list((set(arr1) & set(arr2)))),
        (_OverloadPattern(function_name="array_join"), lambda arr, sep: sep.join(arr)),
        (_OverloadPattern(function_name="array_max"), lambda arr: max(arr)),
        (
            _OverloadPattern(function_name="array_median"),
            lambda arr: (np.median(arr) if (len(arr) > 0) else None),
        ),
        (_OverloadPattern(function_name="array_min"), lambda arr: min(arr)),
        (
            _OverloadPattern(function_name="array_mode", arity=2),
            lambda arr, mode: (
                None
                if (len(arr) <= 0)
                else (
                    statistics.mode(arr)
                    if (mode == 0)
                    else (
                        max(statistics.multimode(arr))
                        if (mode == 1)
                        else (min(statistics.multimode(arr)) if (mode == 2) else None)
                    )
                )
            ),
        ),
        (
            _OverloadPattern(function_name="array_mode", arity=1),
            lambda arr: (statistics.mode(arr) if (len(arr) > 0) else None),
        ),
        (_OverloadPattern(function_name="array_multimode"), lambda arr: statistics.multimode(arr)),
        (_OverloadPattern(function_name="array_normalize"), _ArrayNormalizeOp()),
        (
            _OverloadPattern(function_name="array_position"),
            lambda arr, element: ((arr.index(element) + 1) if (element in arr) else 0),
        ),
        (
            _OverloadPattern(function_name="array_remove"),
            lambda arr, element: [x for x in arr if (x != element)],
        ),
        (_OverloadPattern(function_name="array_sort_desc"), lambda arr: sorted(arr, reverse=True)),
        (_OverloadPattern(function_name="array_sort"), lambda arr: sorted(arr)),
        (
            _OverloadPattern(function_name="array_stddev"),
            lambda arr, is_sample: (None if ((len(arr) - int(is_sample)) <= 0) else np.std(arr, ddof=int(is_sample))),
        ),
        (_OverloadPattern(function_name="array_sum"), lambda arr: sum(arr)),
        (_OverloadPattern(function_name="arrays_overlap"), lambda arr1, arr2: bool((set(arr1) & set(arr2)))),
        (_OverloadPattern(function_name="asin"), math.asin),
        (_OverloadPattern(function_name="atan"), math.atan),
        (_OverloadPattern(function_name="atan2"), math.atan2),
        (_OverloadPattern(function_name="bankers_round"), round),
        (_OverloadPattern(function_name="between"), lambda x, low, high: (low <= x <= high)),
        (_OverloadPattern(function_name="cardinality"), lambda arr: len(arr)),
        (_OverloadPattern(function_name="cbrt"), lambda x: math.pow(x, (1.0 / 3.0))),
        (_OverloadPattern(function_name="ceiling"), math.ceil),
        (_OverloadPattern(function_name="chr"), lambda x: chr(x)),
        (_OverloadPattern(function_name="clamp"), lambda x, min_val, max_val: max(min_val, min(max_val, x))),
        (_OverloadPattern(function_name="coalesce"), _coalesce_op),
        (_OverloadPattern(function_name="concat", return_type=pa.large_string()), lambda *args: "".join(args)),
        *[
            (
                _OverloadPattern(function_name="concat", return_type=list_type(generic("T"))),
                lambda *args: [item for arg in args for item in arg],
            )
            for list_type in PA_LIST_TYPES
        ],
        (_OverloadPattern(function_name="contains"), lambda m, k: (k in m)),
        (_OverloadPattern(function_name="cos"), math.cos),
        (_OverloadPattern(function_name="cosh"), math.cosh),
        (_OverloadPattern(function_name="cosine_similarity_vector"), _CosineSimilarityOp()),
        (_OverloadPattern(function_name="count_all"), lambda x: len(x)),
        (
            _OverloadPattern(function_name="count_distinct"),
            _exact_count_distinct_fn_from_func_name("count_distinct"),
        ),
        (_OverloadPattern(function_name="current_date"), datetime.date.today),
        (_OverloadPattern(function_name="degrees"), math.degrees),
        (
            _OverloadPattern(function_name="distinct_from"),
            lambda a, b: ((a != b) or ((a is None) != (b is None))),
        ),
        (_OverloadPattern(function_name="dot_product_vector"), _DotProductOp()),
        (_OverloadPattern(function_name="e"), lambda: math.e),
        (_OverloadPattern(function_name="element_at"), lambda m, k: m[k]),
        (_OverloadPattern(function_name="ends_with"), lambda s, suffix: s.endswith(suffix)),
        (_OverloadPattern(function_name="eq"), _NullCheckedOp(operator.eq)),
        (_OverloadPattern(function_name="exp"), math.exp),
        (
            _OverloadPattern(function_name="find_first_index"),
            lambda arr, pred: next(((i + 1) for (i, x) in enumerate(arr) if pred(x)), 0),
        ),
        (
            _OverloadPattern(function_name="find_first"),
            lambda arr, pred: next((x for x in arr if pred(x)), None),
        ),
        (_OverloadPattern(function_name="flatten"), lambda arr: [item for sublist in arr for item in sublist]),
        (_OverloadPattern(function_name="floor"), math.floor),
        (_OverloadPattern(function_name="format_datetime"), lambda dt: dt.isoformat()),
        (_OverloadPattern(function_name="from_base"), lambda s, base: int(s, base)),
        (
            _OverloadPattern(name="string_to_bytes_base64", function_name="from_base64"),
            lambda x: base64.b64decode(x.encode()),
        ),
        (_OverloadPattern(function_name="from_big_endian_32"), lambda b: int.from_bytes(b, byteorder="big")),
        (_OverloadPattern(function_name="from_big_endian_64"), lambda b: int.from_bytes(b, byteorder="big")),
        (_OverloadPattern(name="string_to_bytes_hex", function_name="from_hex"), lambda x: bytes.fromhex(x)),
        (_OverloadPattern(function_name="from_utf8"), lambda x: x.decode("utf-8")),
        (
            _OverloadPattern(function_name="greatest"),
            lambda *args: (max(args) if all(((arg is not None) for arg in args)) else None),
        ),
        (_OverloadPattern(function_name="gt"), _NullCheckedOp(operator.gt)),
        (_OverloadPattern(function_name="gte"), _NullCheckedOp(operator.ge)),
        (_OverloadPattern(function_name="gunzip"), lambda x: (gzip.decompress(x) if (x is not None) else None)),
        (_OverloadPattern(function_name="is_nan"), math.isnan),
        (_OverloadPattern(function_name="is_null"), lambda x: (x is None)),
        (
            _OverloadPattern(function_name="jaccard_similarity"),
            lambda left, right: (len((set(left) & set(right))) / max(len((set(left) | set(right))), 1)),
        ),
        (
            _OverloadPattern(function_name="least"),
            lambda *args: (min(args) if all(((arg is not None) for arg in args)) else None),
        ),
        (_OverloadPattern(function_name="length"), len),
        (
            _OverloadPattern(function_name="levenshtein_distance"),
            lambda s1, s2: __import__("difflib").ndiff(s1, s2).__len__(),
        ),
        (_OverloadPattern(function_name="ln"), math.log),
        (_OverloadPattern(function_name="log10"), math.log10),
        (_OverloadPattern(function_name="log2"), math.log2),
        (_OverloadPattern(function_name="lower"), lambda s: s.lower()),
        (
            _OverloadPattern(function_name="lpad"),
            lambda s, size, padstr: (
                ((padstr * (((size - len(s)) // len(padstr)) + 1))[: (size - len(s))] + s) if (len(s) < size) else s
            ),
        ),
        (_OverloadPattern(function_name="lt"), _NullCheckedOp(operator.lt)),
        (_OverloadPattern(function_name="lte"), _NullCheckedOp(operator.le)),
        (_OverloadPattern(function_name="ltrim", arity=2), lambda s, chars: s.lstrip(chars)),
        (_OverloadPattern(function_name="ltrim", arity=1), lambda s: s.lstrip()),
        (_OverloadPattern(function_name="map_contains"), lambda m, k: (k in m)),
        (_OverloadPattern(function_name="map_get"), lambda m, k: m.get(k, None)),
        (_OverloadPattern(function_name="max"), lambda x: pc.max(x).as_py()),
        (_OverloadPattern(function_name="md5"), lambda s: hashlib.md5(s).digest()),
        (_OverloadPattern(function_name="mean"), lambda x: pc.mean(x).as_py()),
        (_OverloadPattern(function_name="vector_mean"), _velox_only_agg("vector_mean")),
        (_OverloadPattern(function_name="min"), lambda x: pc.min(x).as_py()),
        (
            _OverloadPattern(function_name="mode"),
            lambda x: pc.mode(x).field("mode")[0].as_py(),  # type: ignore
        ),
        (_OverloadPattern(function_name="nan"), lambda: float("nan")),
        (_OverloadPattern(function_name="negate"), lambda a: (-a)),
        (_OverloadPattern(function_name="pi"), lambda: math.pi),
        (_OverloadPattern(function_name="pow"), math.pow),
        (_OverloadPattern(function_name="power"), math.pow),
        (_OverloadPattern(function_name="python_element_at"), lambda m, k: m[k]),
        (_OverloadPattern(function_name="python_range"), range),
        (_OverloadPattern(function_name="radians"), math.radians),
        (_OverloadPattern(function_name="rand"), lambda: __import__("random").random()),
        (
            _OverloadPattern(function_name="regexp_replace", arity=3),
            lambda s, pattern, replacement: re.sub(pattern, replacement, s),
        ),
        (_OverloadPattern(function_name="regexp_replace", arity=2), lambda s, pattern: re.sub(pattern, "", s)),
        (_OverloadPattern(function_name="remove_nulls"), lambda arr: [x for x in arr if (x is not None)]),
        (_OverloadPattern(function_name="replace"), lambda s, old, new: s.replace(old, new)),
        (_OverloadPattern(function_name="reverse"), lambda s: s[::(-1)]),
        (
            _OverloadPattern(function_name="round", arity=2),
            lambda a, b: decimal.Decimal(a).quantize(decimal.Decimal(f"1E{(-b)}"), rounding=decimal.ROUND_HALF_UP),
        ),
        (
            _OverloadPattern(function_name="round", arity=1),
            lambda a: decimal.Decimal(a).quantize(0, rounding=decimal.ROUND_UP),
        ),
        (
            _OverloadPattern(function_name="rpad"),
            lambda s, size, padstr: (
                (s + (padstr * (((size - len(s)) // len(padstr)) + 1))[: (size - len(s))]) if (len(s) < size) else s
            ),
        ),
        (_OverloadPattern(function_name="rtrim", arity=2), lambda s, chars: s.rstrip(chars)),
        (_OverloadPattern(function_name="rtrim", arity=1), lambda s: s.rstrip()),
        (_OverloadPattern(function_name="scalar_max"), lambda x, y: max(x, y)),
        (_OverloadPattern(function_name="scalar_min"), lambda x, y: min(x, y)),
        (
            _OverloadPattern(function_name="sequence_matcher_ratio"),
            lambda left, right: difflib.SequenceMatcher(None, left, right).ratio(),
        ),
        (
            _OverloadPattern(function_name="sequence", arity=3),
            lambda start, stop, step: list(range(start, (stop + 1), step)),
        ),
        (
            _OverloadPattern(function_name="sequence", arity=2),
            lambda start, stop: list(range(start, (stop + 1))),
        ),
        (_OverloadPattern(function_name="sha1"), lambda s: hashlib.sha1(s).digest()),
        (_OverloadPattern(function_name="sha256"), lambda s: hashlib.sha256(s).digest()),
        (_OverloadPattern(function_name="sha512"), lambda s: hashlib.sha512(s).digest()),
        (_OverloadPattern(function_name="shuffle"), lambda arr: sorted(arr, key=(lambda x: random.random()))),
        (
            _OverloadPattern(function_name="sign", return_type=pa.int64()),
            lambda x: (1 if (x > 0) else ((-1) if (x < 0) else 0)),
        ),
        (
            _OverloadPattern(function_name="sign", return_type=pa.float64()),
            lambda x: float((1 if (x > 0) else ((-1) if (x < 0) else 0))),
        ),
        (_OverloadPattern(function_name="sin"), math.sin),
        (_OverloadPattern(function_name="slice"), lambda m, start, length: m[(start - 1) : (start + length)]),
        (
            _OverloadPattern(function_name="split_part"),
            lambda s, delimiter, index: (
                s.split(delimiter)[(index - 1)] if (0 < index <= len(s.split(delimiter))) else ""
            ),
        ),
        (_OverloadPattern(function_name="split", arity=3), lambda s, d, n: s.split(d, maxsplit=n)),
        (_OverloadPattern(function_name="split", arity=2), lambda s, d: s.split(d)),
        (_OverloadPattern(function_name="sqrt"), math.sqrt),
        (_OverloadPattern(function_name="starts_with"), lambda s, prefix: s.startswith(prefix)),
        (
            _OverloadPattern(function_name="stddev_sample"),
            lambda x: (None if (len(x) <= 1) else np.std(x, ddof=1).item()),
        ),
        (_OverloadPattern(function_name="strpos"), lambda s, substr: s.find(substr)),
        (_OverloadPattern(function_name="strrpos"), lambda s, substr: s.rfind(substr)),
        (_OverloadPattern(function_name="sum"), lambda x: pc.sum(x, min_count=0).as_py()),
        (_OverloadPattern(function_name="tan"), math.tan),
        (_OverloadPattern(function_name="tanh"), math.tanh),
        (
            _OverloadPattern(function_name="to_base"),
            lambda num, base: (__import__("numpy").base_repr(num, base).lower() if (base <= 36) else None),
        ),
        (
            _OverloadPattern(name="bytes_to_string_base64", function_name="to_base64"),
            lambda x: base64.b64encode(x).decode(),
        ),
        (_OverloadPattern(name="bytes_to_string_hex", function_name="to_hex"), lambda x: x.hex()),
        (_OverloadPattern(function_name="to_utf8"), lambda x: x.encode("utf-8")),
        (
            _OverloadPattern(function_name="total_seconds"),
            lambda x: (x.total_seconds() if (x is not None) else None),
        ),
        (_OverloadPattern(function_name="trail"), lambda s, n: s[(-n):]),
        (_OverloadPattern(function_name="transform"), lambda arr, func: [func(x) for x in arr]),
        (_OverloadPattern(function_name="trim", arity=2), lambda s, chars: s.strip(chars)),
        (_OverloadPattern(function_name="trim", arity=1), lambda s: s.strip()),
        (_OverloadPattern(function_name="truncate"), math.trunc),
        (_OverloadPattern(function_name="upper"), lambda s: s.upper()),
        (
            _OverloadPattern(function_name="variance_sample"),
            lambda x: (None if (len(x) <= 1) else np.var(x, ddof=1).item()),
        ),
        (_OverloadPattern(function_name="vector_sum"), _velox_only_agg("vector_sum")),
        (
            _OverloadPattern(function_name="width_bucket"),
            lambda operand, bound1, bound2, bucket_count: (
                (min(bucket_count, max(0, int((((operand - bound1) / (bound2 - bound1)) * bucket_count)))) + 1)
                if (bound2 != bound1)
                else 1
            ),
        ),
        (_OverloadPattern(function_name="zi_split_part"), lambda s, sep, index: s.split(sep)[index]),
    ],
)

CHALK_SQL_FUNCTIONS = FunctionRegistry(
    default_arrow_type_promoter,
    {
        "+": [
            # SQL does not allow + to be used for string concatenation.
            ov
            for ov in CHALK_FUNCTION_REGISTRY.lookup_overloads("+")
            if isinstance(ov.pybind_function, DirectChalkFunctionImpl) and ov.pybind_function.get_name() == "plus"
        ],
    },
)
"""
The order of resolution is based on the order that they appear in the list. So we attempt to resolve against
CHALK_SQL_FUNCTIONS.get(name)[0], then CHALK_SQL_FUNCTIONS.get(name)[1], etc.

These functions are those that aren't given special treatment by DuckDB. That is, if I say SELECT 1 + 2, DuckDB parses
this as "+"(1,2), instead of a special class of ExpressionNode.
"""

CHALK_SQL_FUNCTION_REGISTRY: FunctionRegistry = CHALK_FUNCTION_REGISTRY.shadowed_by(CHALK_SQL_FUNCTIONS)

"""
The `CHALK_FUNCTION_REGISTRY` lists explicit overloads for a subset of (scalar) Chalk functions.
Each function can have multiple overloads, with different number or types of input parameters.

Overloads are considered in the listed order - the first matching overload is selected.
This means that for e.g. numeric functions which support multiple precisions, list the most-specific overloads first.

The backend function name may be different from the Chalk function name.

This registry should be preferred, because it is used by chalkpy->UnderscoreValue,
UnderscoreValue->libchalk/velox, and ast.AST->SymbolicValue conversion logic,
which ensures that the overloads do not get out-of-sync.
"""


def get_chalk_function_registry_overload(
    *,
    function_name: str,
    input_types: MaybeNamedCollection[ArgumentType],
) -> None | ChalkFunctionOverloadResolved | ChalkFunctionOverloadFailed:
    """
    If no matching function exists in the registry, returns `None`.

    Otherwise, attempts to resolve the provided input types against the overloads
    in the registry.

    If there is a Chalk function registered with the provided name, then returns
    either a `ChalkFunctionOverloadResolved` with the resolved input/output types,
    or else returns an `ChalkFunctionOverloadFailed` with information about the attempted overloads.
    """
    return CHALK_FUNCTION_REGISTRY.resolve(function_name=function_name, input_types=input_types)
