"""gRPC-based operations for LangGraph API."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import AsyncIterator
from datetime import UTC
from http import HTTPStatus
from typing import Any
from uuid import UUID

import orjson
import structlog
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct  # type: ignore[import]
from grpc import StatusCode
from grpc.aio import AioRpcError
from langgraph_sdk.schema import Config
from starlette.exceptions import HTTPException

from langgraph_api.schema import (
    Assistant,
    AssistantSelectField,
    Context,
    MetadataInput,
    OnConflictBehavior,
)

from .client import GrpcClient
from .generated import core_api_pb2 as pb

GRPC_STATUS_TO_HTTP_STATUS = {
    StatusCode.NOT_FOUND: HTTPStatus.NOT_FOUND,
    StatusCode.ALREADY_EXISTS: HTTPStatus.CONFLICT,
    StatusCode.INVALID_ARGUMENT: HTTPStatus.UNPROCESSABLE_ENTITY,
}

logger = structlog.stdlib.get_logger(__name__)


def map_if_exists(if_exists: str) -> pb.OnConflictBehavior:
    if if_exists == "do_nothing":
        return pb.OnConflictBehavior.DO_NOTHING
    return pb.OnConflictBehavior.RAISE


def map_configurable(config: Config) -> Struct:
    """Build pb.Config, placing non-standard keys into `extra` bytes.

    The `extra` field mirrors any keys that are not first-class in
    Config (e.g., "tags", "recursion_limit", "configurable").
    It is JSON-encoded bytes to minimize serde overhead; the server will
    unpack and persist them as top-level keys.
    """
    base_keys = {"tags", "recursion_limit", "configurable"}
    extra_dict = {k: v for k, v in (config or {}).items() if k not in base_keys}

    kwargs: dict[str, Any] = dict(
        tags=config.get("tags"),
        recursion_limit=config.get("recursion_limit"),
        configurable=(
            dict_to_struct(config.get("configurable", {}))
            if config.get("configurable")
            else None
        ),
    )
    if extra_dict:
        kwargs["extra"] = orjson.dumps(extra_dict)

    return pb.Config(**kwargs)


def consolidate_config_and_context(
    config: Config | None, context: Context | None
) -> tuple[Config, Context | None]:
    """Return a new (config, context) with consistent configurable/context.

    Does not mutate the passed-in objects. If both configurable and context
    are provided, raises 400. If only one is provided, mirrors it to the other.
    """
    cfg: Config = dict(config or {})
    ctx: Context | None = dict(context) if context is not None else None

    if cfg.get("configurable") and ctx:
        raise HTTPException(
            status_code=400,
            detail="Cannot specify both configurable and context. Prefer setting context alone. Context was introduced in LangGraph 0.6.0 and is the long term planned replacement for configurable.",
        )

    if cfg.get("configurable"):
        ctx = cfg["configurable"]
    elif ctx is not None:
        cfg["configurable"] = ctx

    return cfg, ctx


def dict_to_struct(data: dict[str, Any]) -> Struct:
    """Convert a dictionary to a protobuf Struct."""
    struct = Struct()
    if data:
        struct.update(data)
    return struct


def struct_to_dict(struct: Struct) -> dict[str, Any]:
    """Convert a protobuf Struct to a dictionary."""
    return MessageToDict(struct) if struct else {}


def _runnable_config_to_user_dict(cfg: pb.Config | None) -> dict[str, Any]:
    """Convert pb.Config to user-visible dict, unpacking `extra`.

    - Keeps top-level known keys: tags, recursion_limit, configurable.
    - Merges keys from `extra` into the top-level dict.
    """
    if not cfg:
        return {}

    out: dict[str, Any] = {}
    # tags
    if cfg.tags:
        out["tags"] = list(cfg.tags)
    # recursion_limit (preserve presence of 0 if set)
    try:
        if cfg.HasField("recursion_limit"):
            out["recursion_limit"] = cfg.recursion_limit
    except ValueError:
        # Some runtimes may not support HasField on certain builds; fallback
        if getattr(cfg, "recursion_limit", None) is not None:
            out["recursion_limit"] = cfg.recursion_limit
    # configurable
    if cfg.HasField("configurable"):
        out["configurable"] = struct_to_dict(cfg.configurable)
    # extra (bytes: JSON-encoded object)
    if cfg.HasField("extra") and cfg.extra:
        extra = orjson.loads(cfg.extra)
        if isinstance(extra, dict) and extra:
            out.update(extra)

    return out


def proto_to_assistant(proto_assistant: pb.Assistant) -> Assistant:
    """Convert protobuf Assistant to dictionary format."""
    # Preserve None for optional scalar fields by checking presence via HasField
    description = (
        proto_assistant.description if proto_assistant.HasField("description") else None
    )
    return {
        "assistant_id": proto_assistant.assistant_id,
        "graph_id": proto_assistant.graph_id,
        "version": proto_assistant.version,
        "created_at": proto_assistant.created_at.ToDatetime(tzinfo=UTC),
        "updated_at": proto_assistant.updated_at.ToDatetime(tzinfo=UTC),
        "config": _runnable_config_to_user_dict(proto_assistant.config),
        "context": struct_to_dict(proto_assistant.context),
        "metadata": struct_to_dict(proto_assistant.metadata),
        "name": proto_assistant.name,
        "description": description,
    }


def _map_sort_by(sort_by: str | None) -> pb.AssistantsSortBy:
    """Map string sort_by to protobuf enum."""
    if not sort_by:
        return pb.AssistantsSortBy.CREATED_AT

    sort_by_lower = sort_by.lower()
    mapping = {
        "assistant_id": pb.AssistantsSortBy.ASSISTANT_ID,
        "graph_id": pb.AssistantsSortBy.GRAPH_ID,
        "name": pb.AssistantsSortBy.NAME,
        "created_at": pb.AssistantsSortBy.CREATED_AT,
        "updated_at": pb.AssistantsSortBy.UPDATED_AT,
    }
    return mapping.get(sort_by_lower, pb.AssistantsSortBy.CREATED_AT)


def _map_sort_order(sort_order: str | None) -> pb.SortOrder:
    """Map string sort_order to protobuf enum."""
    if sort_order and sort_order.upper() == "ASC":
        return pb.SortOrder.ASC
    return pb.SortOrder.DESC


def _handle_grpc_error(error: AioRpcError) -> None:
    """Handle gRPC errors and convert to appropriate exceptions."""
    raise HTTPException(
        status_code=GRPC_STATUS_TO_HTTP_STATUS.get(
            error.code(), HTTPStatus.INTERNAL_SERVER_ERROR
        ),
        detail=str(error.details()),
    )


class Authenticated:
    """Base class for authenticated operations (matches storage_postgres interface)."""

    resource: str = "assistants"

    @classmethod
    async def handle_event(
        cls,
        ctx: Any,  # Auth context
        action: str,
        value: Any,
    ) -> dict[str, Any] | None:
        """Handle authentication event - stub implementation for now."""
        # TODO: Implement proper auth handling that converts auth context
        # to gRPC AuthFilter format when needed
        return None


def grpc_error_guard(cls):
    """Class decorator to wrap async methods and handle gRPC errors uniformly."""
    for name, attr in list(cls.__dict__.items()):
        func = None
        wrapper_type = None
        if isinstance(attr, staticmethod):
            func = attr.__func__
            wrapper_type = staticmethod
        elif isinstance(attr, classmethod):
            func = attr.__func__
            wrapper_type = classmethod
        elif callable(attr):
            func = attr

        if func and asyncio.iscoroutinefunction(func):

            def make_wrapper(f):
                @functools.wraps(f)
                async def wrapped(*args, **kwargs):
                    try:
                        return await f(*args, **kwargs)
                    except AioRpcError as e:
                        _handle_grpc_error(e)

                return wrapped  # noqa: B023

            wrapped = make_wrapper(func)
            if wrapper_type is staticmethod:
                setattr(cls, name, staticmethod(wrapped))
            elif wrapper_type is classmethod:
                setattr(cls, name, classmethod(wrapped))
            else:
                setattr(cls, name, wrapped)
    return cls


@grpc_error_guard
class Assistants(Authenticated):
    """gRPC-based assistants operations."""

    resource = "assistants"

    @staticmethod
    async def search(
        conn,  # Not used in gRPC implementation
        *,
        graph_id: str | None,
        metadata: MetadataInput,
        limit: int,
        offset: int,
        sort_by: str | None = None,
        sort_order: str | None = None,
        select: list[AssistantSelectField] | None = None,
        ctx: Any = None,
    ) -> tuple[AsyncIterator[Assistant], int | None]:  # type: ignore[return-value]
        """Search assistants via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx,
            "search",
            {
                "graph_id": graph_id,
                "metadata": metadata,
                "limit": limit,
                "offset": offset,
            },
        )

        # Build the gRPC request
        request = pb.SearchAssistantsRequest(
            filters=auth_filters,
            graph_id=graph_id,
            metadata=dict_to_struct(metadata or {}),
            limit=limit,
            offset=offset,
            sort_by=_map_sort_by(sort_by),
            sort_order=_map_sort_order(sort_order),
            select=select,
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.Search(request)

        # Convert response to expected format
        assistants = [
            proto_to_assistant(assistant) for assistant in response.assistants
        ]

        # Determine if there are more results
        # Note: gRPC doesn't return cursor info, so we estimate based on result count
        cursor = offset + limit if len(assistants) == limit else None

        async def generate_results():
            for assistant in assistants:
                yield {
                    k: v for k, v in assistant.items() if select is None or k in select
                }

        return generate_results(), cursor

    @staticmethod
    async def get(
        conn,  # Not used in gRPC implementation
        assistant_id: UUID | str,
        ctx: Any = None,
    ) -> AsyncIterator[Assistant]:  # type: ignore[return-value]
        """Get assistant by ID via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx, "read", {"assistant_id": str(assistant_id)}
        )

        # Build the gRPC request
        request = pb.GetAssistantRequest(
            assistant_id=str(assistant_id),
            filters=auth_filters or {},
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.Get(request)

        # Convert and yield the result
        assistant = proto_to_assistant(response)

        async def generate_result():
            yield assistant

        return generate_result()

    @staticmethod
    async def put(
        conn,  # Not used in gRPC implementation
        assistant_id: UUID | str,
        *,
        graph_id: str,
        config: Config,
        context: Context,
        metadata: MetadataInput,
        if_exists: OnConflictBehavior,
        name: str,
        description: str | None = None,
        ctx: Any = None,
    ) -> AsyncIterator[Assistant]:  # type: ignore[return-value]
        """Create/update assistant via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx,
            "create",
            {
                "assistant_id": str(assistant_id),
                "graph_id": graph_id,
                "config": config,
                "context": context,
                "metadata": metadata,
                "name": name,
                "description": description,
            },
        )

        config, context = consolidate_config_and_context(config, context)

        on_conflict = map_if_exists(if_exists)

        # Build the gRPC request
        request = pb.CreateAssistantRequest(
            assistant_id=str(assistant_id),
            graph_id=graph_id,
            filters=auth_filters or {},
            if_exists=on_conflict,
            config=map_configurable(config),
            context=dict_to_struct(context or {}),
            name=name,
            description=description,
            metadata=dict_to_struct(metadata or {}),
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.Create(request)

        # Convert and yield the result
        assistant = proto_to_assistant(response)

        async def generate_result():
            yield assistant

        return generate_result()

    @staticmethod
    async def patch(
        conn,  # Not used in gRPC implementation
        assistant_id: UUID | str,
        *,
        config: dict | None = None,
        context: Context | None = None,
        graph_id: str | None = None,
        metadata: MetadataInput | None = None,
        name: str | None = None,
        description: str | None = None,
        ctx: Any = None,
    ) -> AsyncIterator[Assistant]:  # type: ignore[return-value]
        """Update assistant via gRPC."""
        metadata = metadata if metadata is not None else {}
        config = config if config is not None else {}
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx,
            "update",
            {
                "assistant_id": str(assistant_id),
                "graph_id": graph_id,
                "config": config,
                "context": context,
                "metadata": metadata,
                "name": name,
                "description": description,
            },
        )

        config, context = consolidate_config_and_context(config, context)

        # Build the gRPC request
        request = pb.PatchAssistantRequest(
            assistant_id=str(assistant_id),
            filters=auth_filters or {},
            graph_id=graph_id,
            name=name,
            description=description,
            metadata=dict_to_struct(metadata or {}),
        )

        # Add optional config if provided
        if config:
            request.config.CopyFrom(map_configurable(config))

        # Add optional context if provided
        if context:
            request.context.CopyFrom(dict_to_struct(context))

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.Patch(request)

        # Convert and yield the result
        assistant = proto_to_assistant(response)

        async def generate_result():
            yield assistant

        return generate_result()

    @staticmethod
    async def delete(
        conn,  # Not used in gRPC implementation
        assistant_id: UUID | str,
        ctx: Any = None,
    ) -> AsyncIterator[UUID]:  # type: ignore[return-value]
        """Delete assistant via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx, "delete", {"assistant_id": str(assistant_id)}
        )

        # Build the gRPC request
        request = pb.DeleteAssistantRequest(
            assistant_id=str(assistant_id),
            filters=auth_filters or {},
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            await client.assistants.Delete(request)

        # Return the deleted ID
        async def generate_result():
            yield UUID(str(assistant_id))

        return generate_result()

    @staticmethod
    async def set_latest(
        conn,  # Not used in gRPC implementation
        assistant_id: UUID | str,
        version: int,
        ctx: Any = None,
    ) -> AsyncIterator[Assistant]:  # type: ignore[return-value]
        """Set latest version of assistant via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx,
            "update",
            {
                "assistant_id": str(assistant_id),
                "version": version,
            },
        )

        # Build the gRPC request
        request = pb.SetLatestAssistantRequest(
            assistant_id=str(assistant_id),
            version=version,
            filters=auth_filters or {},
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.SetLatest(request)

        # Convert and yield the result
        assistant = proto_to_assistant(response)

        async def generate_result():
            yield assistant

        return generate_result()

    @staticmethod
    async def get_versions(
        conn,  # Not used in gRPC implementation
        assistant_id: UUID | str,
        metadata: MetadataInput,
        limit: int,
        offset: int,
        ctx: Any = None,
    ) -> AsyncIterator[Assistant]:  # type: ignore[return-value]
        """Get all versions of assistant via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx,
            "search",
            {"assistant_id": str(assistant_id), "metadata": metadata},
        )

        # Build the gRPC request
        request = pb.GetAssistantVersionsRequest(
            assistant_id=str(assistant_id),
            filters=auth_filters or {},
            metadata=dict_to_struct(metadata or {}),
            limit=limit,
            offset=offset,
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.GetVersions(request)

        # Convert and yield the results
        async def generate_results():
            for version in response.versions:
                # Preserve None for optional scalar fields by checking presence
                version_description = (
                    version.description if version.HasField("description") else None
                )
                yield {
                    "assistant_id": version.assistant_id,
                    "graph_id": version.graph_id,
                    "version": version.version,
                    "created_at": version.created_at.ToDatetime(tzinfo=UTC),
                    "config": _runnable_config_to_user_dict(version.config),
                    "context": struct_to_dict(version.context),
                    "metadata": struct_to_dict(version.metadata),
                    "name": version.name,
                    "description": version_description,
                }

        return generate_results()

    @staticmethod
    async def count(
        conn,  # Not used in gRPC implementation
        *,
        graph_id: str | None = None,
        metadata: MetadataInput = None,
        ctx: Any = None,
    ) -> int:  # type: ignore[return-value]
        """Count assistants via gRPC."""
        # Handle auth filters
        auth_filters = await Assistants.handle_event(
            ctx, "search", {"graph_id": graph_id, "metadata": metadata}
        )

        # Build the gRPC request
        request = pb.CountAssistantsRequest(
            filters=auth_filters or {},
            graph_id=graph_id,
            metadata=dict_to_struct(metadata or {}),
        )

        # Make the gRPC call
        async with GrpcClient() as client:
            response = await client.assistants.Count(request)

        return int(response.count)
