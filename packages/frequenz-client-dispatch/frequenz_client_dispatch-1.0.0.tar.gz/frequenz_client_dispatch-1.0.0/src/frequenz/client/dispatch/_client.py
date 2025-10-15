# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Dispatch API client for Python."""
from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Awaitable, Iterable, Iterator, Literal, cast

# pylint: disable-next=no-name-in-module
from frequenz.api.common.v1alpha8.pagination.pagination_params_pb2 import (
    PaginationParams,
)
from frequenz.api.common.v1alpha8.types.interval_pb2 import Interval as PBInterval
from frequenz.api.dispatch.v1 import dispatch_pb2_grpc
from frequenz.api.dispatch.v1.dispatch_pb2 import (
    CreateMicrogridDispatchResponse,
    DeleteMicrogridDispatchRequest,
    DispatchFilter,
    GetMicrogridDispatchRequest,
    GetMicrogridDispatchResponse,
    ListMicrogridDispatchesRequest,
    ListMicrogridDispatchesResponse,
    StreamMicrogridDispatchesRequest,
    StreamMicrogridDispatchesResponse,
    UpdateMicrogridDispatchRequest,
    UpdateMicrogridDispatchResponse,
)

from frequenz import channels
from frequenz.client.base.channel import ChannelOptions, SslOptions
from frequenz.client.base.client import BaseApiClient
from frequenz.client.base.conversion import to_timestamp
from frequenz.client.base.exception import ClientNotConnected
from frequenz.client.base.retry import LinearBackoff
from frequenz.client.base.streaming import GrpcStreamBroadcaster
from frequenz.client.common.microgrid import MicrogridId

from ._internal_types import DispatchCreateRequest
from .recurrence import RecurrenceRule
from .types import (
    Dispatch,
    DispatchEvent,
    DispatchId,
    TargetComponents,
    _target_components_to_protobuf,
)

# pylint: enable=no-name-in-module
DEFAULT_DISPATCH_PORT = 443


class DispatchApiClient(BaseApiClient[dispatch_pb2_grpc.MicrogridDispatchServiceStub]):
    """Dispatch API client."""

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        *,
        server_url: str,
        auth_key: str | None = None,
        key: str | None = None,
        sign_secret: str | None = None,
        connect: bool = True,
        call_timeout: timedelta = timedelta(seconds=60),
        stream_timeout: timedelta = timedelta(minutes=5),
    ) -> None:
        """Initialize the client.

        Args:
            server_url: The URL of the server to connect to.
            auth_key: API key to use for authentication.
            key: Deprecated, use `auth_key` instead.
            sign_secret: Optional secret for signing requests.
            connect: Whether to connect to the service immediately.
            call_timeout: Timeout for gRPC calls, default is 60 seconds.
            stream_timeout: Timeout for gRPC streams, default is 5 minutes.

        Raises:
            TypeError: If neither `auth_key` nor `key` is provided.
        """
        if key is not None:
            warnings.warn(
                "The `key` parameter is deprecated, use `auth_key` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        auth_key = auth_key or key
        if auth_key is None:
            raise TypeError(
                "__init__() missing 1 required keyword-only argument: 'auth_key'"
            )

        super().__init__(
            server_url,
            dispatch_pb2_grpc.MicrogridDispatchServiceStub,
            connect=connect,
            channel_defaults=ChannelOptions(
                port=DEFAULT_DISPATCH_PORT,
                ssl=SslOptions(enabled=True),
            ),
            auth_key=auth_key,
            sign_secret=sign_secret,
        )
        self._streams: dict[
            MicrogridId,
            GrpcStreamBroadcaster[StreamMicrogridDispatchesResponse, DispatchEvent],
        ] = {}
        """A dictionary of streamers, keyed by microgrid_id."""

        self._call_timeout_seconds = call_timeout.total_seconds()
        self._stream_timeout_seconds = stream_timeout.total_seconds()

    @property
    def call_timeout(self) -> timedelta:
        """Get the call timeout."""
        return timedelta(seconds=self._call_timeout_seconds)

    @property
    def stream_timeout(self) -> timedelta:
        """Get the stream timeout."""
        return timedelta(seconds=self._stream_timeout_seconds)

    @property
    def stub(self) -> dispatch_pb2_grpc.MicrogridDispatchServiceAsyncStub:
        """The stub for the service."""
        if self._channel is None or self._stub is None:
            raise ClientNotConnected(server_url=self.server_url, operation="stub")
        # This type: ignore is needed because we need to cast the sync stub to
        # the async stub, but we can't use cast because the async stub doesn't
        # actually exists to the eyes of the interpreter, it only exists for the
        # type-checker, so it can only be used for type hints.
        return self._stub  # type: ignore

    # pylint: disable=too-many-arguments, too-many-locals
    async def list(
        self,
        microgrid_id: MicrogridId,
        *,
        target_components: Iterable[TargetComponents] = (),
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        end_from: datetime | None = None,
        end_to: datetime | None = None,
        active: bool | None = None,
        dry_run: bool | None = None,
        dispatch_ids: Iterable[DispatchId] = (),
        filter_queries: Iterable[str] = (),
        page_size: int | None = None,
    ) -> AsyncIterator[Iterator[Dispatch]]:
        """List dispatches.

        This function handles pagination internally and returns an async iterator
        over the dispatches. Pagination parameters like `page_size` and `page_token`
        can be used, but they are mutually exclusive.

        Example usage:

        ```python
        client = DispatchApiClient(
            auth_key="key",
            sign_secret="secret", # Optional so far
            server_url="grpc://dispatch.url.goes.here.example.com"
        )
        async for page in client.list(microgrid_id=MicrogridId(1)):
            for dispatch in page:
                print(dispatch)
        ```

        The `filter_queries` parameter is applied to the dispatch `id` and `type` fields.
        Each query in the list is applied as a logical OR.

        ID tokens are preceded by a `#` so we can tell if an id is intended or a type.

        - input of [`#4`] will match only the record with id of `4`
        - input of [`#not_an_id`] will match types containing `#not_an_id`
        - input of [`bar`] will match `bar` and `foobar`
        - input of [`#4`, `#24`, `bar`, `foo`] will match ids of `4` and `24` and
          types `foo` `bar` `foobar` `foolish bartender`

        Args:
            microgrid_id: The microgrid_id to list dispatches for.
            target_components: optional, list of component ids or categories to filter by.
            start_from: optional, filter by start_time >= start_from.
            start_to: optional, filter by start_time < start_to.
            end_from: optional, filter by end_time >= end_from.
            end_to: optional, filter by end_time < end_to.
            active: optional, filter by active status.
            dry_run: optional, filter by dry_run status.
            dispatch_ids: optional, list of dispatch IDs to filter by.
            filter_queries: optional, list of text queries to filter by.
            page_size: optional, number of dispatches to return per page.

        Returns:
            An async iterator over pages of dispatches.

        Yields:
            A page of dispatches over which you can lazily iterate.
        """

        def to_interval(
            from_: datetime | None, to: datetime | None
        ) -> PBInterval | None:
            return (
                PBInterval(start_time=to_timestamp(from_), end_time=to_timestamp(to))
                if from_ or to
                else None
            )

        # Setup parameters
        start_time_interval = to_interval(start_from, start_to)
        end_time_interval = to_interval(end_from, end_to)
        targets = list(map(_target_components_to_protobuf, target_components))
        filters = DispatchFilter(
            targets=targets,
            start_time_interval=start_time_interval,
            end_time_interval=end_time_interval,
            is_active=active,
            is_dry_run=dry_run,
            dispatch_ids=list(map(int, dispatch_ids)),
            queries=list(filter_queries),
        )

        request = ListMicrogridDispatchesRequest(
            microgrid_id=int(microgrid_id),
            filter=filters,
            pagination_params=(
                PaginationParams(page_size=page_size) if page_size else None
            ),
        )

        while True:
            response = await cast(
                Awaitable[ListMicrogridDispatchesResponse],
                self.stub.ListMicrogridDispatches(
                    request, timeout=self._call_timeout_seconds
                ),
            )

            yield (Dispatch.from_protobuf(dispatch) for dispatch in response.dispatches)

            if len(response.pagination_info.next_page_token):
                request.pagination_params.CopyFrom(
                    PaginationParams(
                        page_token=response.pagination_info.next_page_token
                    )
                )
            else:
                break

    def stream(self, microgrid_id: MicrogridId) -> channels.Receiver[DispatchEvent]:
        """Receive a stream of dispatch events.

        This function returns a receiver channel that can be used to receive
        dispatch events.
        An event is one of [CREATE, UPDATE, DELETE].

        Example usage:

        ```
        client = DispatchApiClient(
            key="key",
            server_url="grpc://dispatch.url.goes.here.example.com"
        )
        async for message in client.stream(microgrid_id=1):
            print(message.event, message.dispatch)
        ```

        Args:
            microgrid_id: The microgrid_id to receive dispatches for.

        Returns:
            A receiver channel to receive the stream of dispatch events.
        """
        return self._get_stream(microgrid_id).new_receiver()

    def _get_stream(
        self, microgrid_id: MicrogridId
    ) -> GrpcStreamBroadcaster[StreamMicrogridDispatchesResponse, DispatchEvent]:
        """Get an instance to the streaming helper."""
        broadcaster = self._streams.get(microgrid_id)
        if broadcaster is not None and not broadcaster.is_running:
            del self._streams[microgrid_id]
            broadcaster = None
        if broadcaster is None:
            request = StreamMicrogridDispatchesRequest(microgrid_id=int(microgrid_id))
            broadcaster = GrpcStreamBroadcaster(
                stream_name="StreamMicrogridDispatches",
                stream_method=lambda: cast(
                    AsyncIterator[StreamMicrogridDispatchesResponse],
                    self.stub.StreamMicrogridDispatches(
                        request,
                        timeout=self._stream_timeout_seconds,
                    ),
                ),
                transform=DispatchEvent.from_protobuf,
                retry_strategy=LinearBackoff(interval=1, limit=None),
            )
            self._streams[microgrid_id] = broadcaster

        return broadcaster

    async def create(  # pylint: disable=too-many-positional-arguments
        self,
        microgrid_id: MicrogridId,
        type: str,  # pylint: disable=redefined-builtin
        start_time: datetime | Literal["NOW"],
        duration: timedelta | None,
        target: TargetComponents,
        *,
        active: bool = True,
        dry_run: bool = False,
        payload: dict[str, Any] | None = None,
        recurrence: RecurrenceRule | None = None,
    ) -> Dispatch:
        """Create a dispatch.

        Args:
            microgrid_id: The microgrid_id to create the dispatch for.
            type: User defined string to identify the dispatch type.
            start_time: The start time of the dispatch. Can be "NOW" for immediate start.
            duration: The duration of the dispatch. Can be `None` for infinite
                or no-duration dispatches (e.g. switching a component on).
            target: The component target for the dispatch.
            active: The active status of the dispatch.
            dry_run: The dry_run status of the dispatch.
            payload: The payload of the dispatch.
            recurrence: The recurrence rule of the dispatch.

        Returns:
            Dispatch: The created dispatch

        Raises:
            ValueError: If start_time is in the past.
        """
        if isinstance(start_time, datetime):
            if start_time <= datetime.now(tz=start_time.tzinfo):
                raise ValueError("start_time must not be in the past")

            # Raise if it's not UTC
            if (
                start_time.tzinfo is None
                or start_time.tzinfo.utcoffset(start_time) is None
            ):
                raise ValueError("start_time must be timezone aware")

        request = DispatchCreateRequest(
            microgrid_id=microgrid_id,
            type=type,
            start_time=start_time,
            duration=duration,
            target=target,
            active=active,
            dry_run=dry_run,
            payload=payload or {},
            recurrence=recurrence,
        )

        response = await cast(
            Awaitable[CreateMicrogridDispatchResponse],
            self.stub.CreateMicrogridDispatch(
                request.to_protobuf(),
                timeout=self._call_timeout_seconds,
            ),
        )

        return Dispatch.from_protobuf(response.dispatch)

    async def update(
        self,
        *,
        microgrid_id: MicrogridId,
        dispatch_id: DispatchId,
        new_fields: dict[str, Any],
    ) -> Dispatch:
        """Update a dispatch.

        The `new_fields` argument is a dictionary of fields to update. The keys are
        the field names, and the values are the new values for the fields.

        For recurrence fields, the keys are preceeded by "recurrence.".

        Note that updating `type` and `dry_run` is not supported.

        Args:
            microgrid_id: The microgrid_id to update the dispatch for.
            dispatch_id: The dispatch_id to update.
            new_fields: The fields to update.

        Returns:
            Dispatch: The updated dispatch.

        Raises:
            ValueError: If updating `type` or `dry_run`.
        """
        msg = UpdateMicrogridDispatchRequest(
            dispatch_id=int(dispatch_id), microgrid_id=int(microgrid_id)
        )

        for key, val in new_fields.items():
            path = key.split(".")

            match path[0]:
                case "start_time":
                    msg.update.start_time.CopyFrom(to_timestamp(val))
                case "duration":
                    if val is None:
                        msg.update.ClearField("duration")
                    else:
                        msg.update.duration = round(val.total_seconds())
                case "target":
                    msg.update.target.CopyFrom(_target_components_to_protobuf(val))
                case "is_active":
                    msg.update.is_active = val
                case "payload":
                    msg.update.payload.update(val)
                case "active":
                    msg.update.is_active = val
                    key = "is_active"
                case "recurrence":
                    match path[1]:
                        case "freq":
                            msg.update.recurrence.freq = val
                        # Proto uses "freq" instead of "frequency"
                        case "frequency":
                            msg.update.recurrence.freq = val
                            # Correct the key to "recurrence.freq"
                            key = "recurrence.freq"
                        case "interval":
                            msg.update.recurrence.interval = val
                        case "end_criteria":
                            msg.update.recurrence.end_criteria.CopyFrom(
                                val.to_protobuf()
                            )
                        case "byminutes":
                            msg.update.recurrence.byminutes.extend(val)
                        case "byhours":
                            msg.update.recurrence.byhours.extend(val)
                        case "byweekdays":
                            msg.update.recurrence.byweekdays.extend(val)
                        case "bymonthdays":
                            msg.update.recurrence.bymonthdays.extend(val)
                        case "bymonths":
                            msg.update.recurrence.bymonths.extend(val)
                        case _:
                            raise ValueError(f"Unknown recurrence field: {path[1]}")
                case _:
                    raise ValueError(f"Unknown field: {path[0]}")

            msg.update_mask.paths.append(key)

        response = await cast(
            Awaitable[UpdateMicrogridDispatchResponse],
            self.stub.UpdateMicrogridDispatch(msg, timeout=self._call_timeout_seconds),
        )

        return Dispatch.from_protobuf(response.dispatch)

    async def get(
        self, *, microgrid_id: MicrogridId, dispatch_id: DispatchId
    ) -> Dispatch:
        """Get a dispatch.

        Args:
            microgrid_id: The microgrid_id to get the dispatch for.
            dispatch_id: The dispatch_id to get.

        Returns:
            Dispatch: The dispatch.
        """
        request = GetMicrogridDispatchRequest(
            dispatch_id=int(dispatch_id), microgrid_id=int(microgrid_id)
        )
        response = await cast(
            Awaitable[GetMicrogridDispatchResponse],
            self.stub.GetMicrogridDispatch(request, timeout=self._call_timeout_seconds),
        )
        return Dispatch.from_protobuf(response.dispatch)

    async def delete(
        self, *, microgrid_id: MicrogridId, dispatch_id: DispatchId
    ) -> None:
        """Delete a dispatch.

        Args:
            microgrid_id: The microgrid_id to delete the dispatch for.
            dispatch_id: The dispatch_id to delete.
        """
        request = DeleteMicrogridDispatchRequest(
            dispatch_id=int(dispatch_id), microgrid_id=int(microgrid_id)
        )
        await cast(
            Awaitable[None],
            self.stub.DeleteMicrogridDispatch(
                request, timeout=self._call_timeout_seconds
            ),
        )
