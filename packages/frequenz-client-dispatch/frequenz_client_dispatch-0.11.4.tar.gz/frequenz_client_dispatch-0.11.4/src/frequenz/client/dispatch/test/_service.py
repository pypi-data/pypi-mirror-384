# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Mock classes for the dispatch api.

Useful for testing.
"""
import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import AsyncIterator

import grpc
import grpc.aio

# pylint: disable=no-name-in-module
from frequenz.api.common.v1alpha8.pagination.pagination_info_pb2 import PaginationInfo
from frequenz.api.dispatch.v1.dispatch_pb2 import (
    CreateMicrogridDispatchRequest as PBDispatchCreateRequest,
)
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
from frequenz.channels import Broadcast
from google.protobuf.empty_pb2 import Empty

# pylint: enable=no-name-in-module
from frequenz.client.base.conversion import to_datetime as _to_dt
from frequenz.client.common.microgrid import MicrogridId
from frequenz.client.common.streaming import Event

from .._internal_types import DispatchCreateRequest
from ..types import Dispatch, DispatchEvent, DispatchId

_logger = logging.getLogger(__name__)


class FakeService:
    """Dispatch mock service for testing."""

    @dataclass(frozen=True)
    class StreamEvent:
        """Event for the stream."""

        microgrid_id: MicrogridId
        """The microgrid id."""

        event: DispatchEvent
        """The event."""

    def __init__(self) -> None:
        """Initialize the stream sender."""
        self._stream_channel: Broadcast[FakeService.StreamEvent] = Broadcast(
            name="fakeservice-dispatch-stream"
        )
        self._stream_sender = self._stream_channel.new_sender()

        self.dispatches: dict[MicrogridId, list[Dispatch]] = {}
        """List of dispatches per microgrid."""

        self._last_id: DispatchId = DispatchId(0)
        """Last used dispatch id."""

    def refresh_last_id_for(self, microgrid_id: MicrogridId) -> None:
        """Update last id to be the next highest number."""
        dispatches = self.dispatches.get(microgrid_id, [])

        if len(dispatches) == 0:
            return

        self._last_id = max(self._last_id, max(dispatch.id for dispatch in dispatches))

    # pylint: disable=invalid-name
    async def ListMicrogridDispatches(
        self,
        request: ListMicrogridDispatchesRequest,
        timeout: int = 5,  # pylint: disable=unused-argument
    ) -> ListMicrogridDispatchesResponse:
        """List microgrid dispatches.

        Args:
            request: The request.
            timeout: timeout for the request, ignored in this mock.

        Returns:
            The dispatch list.
        """
        grid_dispatches = self.dispatches.get(MicrogridId(request.microgrid_id), [])

        return ListMicrogridDispatchesResponse(
            dispatches=map(
                lambda d: d.to_protobuf(),
                filter(
                    lambda d: self._filter_dispatch(d, request),
                    grid_dispatches,
                ),
            ),
            pagination_info=PaginationInfo(
                total_items=len(grid_dispatches), next_page_token=None
            ),
        )

    async def StreamMicrogridDispatches(
        self,
        request: StreamMicrogridDispatchesRequest,
        timeout: int = 5,  # pylint: disable=unused-argument
    ) -> AsyncIterator[StreamMicrogridDispatchesResponse]:
        """Stream microgrid dispatches changes.

        Args:
            request: The request.
            timeout: timeout for the request, ignored in this mock.

        Returns:
            An async generator for dispatch changes.

        Yields:
            An event for each dispatch change.
        """
        receiver = self._stream_channel.new_receiver()

        async for message in receiver:
            _logger.debug("Received message: %s", message)
            if message.microgrid_id == MicrogridId(request.microgrid_id):
                response = StreamMicrogridDispatchesResponse(
                    event=message.event.event.value,
                    dispatch=message.event.dispatch.to_protobuf(),
                )
                yield response

    # pylint: disable=too-many-branches
    @staticmethod
    def _filter_dispatch(
        dispatch: Dispatch, request: ListMicrogridDispatchesRequest
    ) -> bool:
        """Filter a dispatch based on the request."""
        if request.HasField("filter"):
            _filter = request.filter
            for target in _filter.targets:
                if target != dispatch.target:
                    return False
            if _filter.HasField("start_time_interval"):
                if _filter.start_time_interval.HasField("start_time"):
                    start_from = _filter.start_time_interval.start_time
                    if dispatch.start_time < _to_dt(start_from):
                        return False
                if _filter.start_time_interval.HasField("end_time"):
                    start_to = _filter.start_time_interval.end_time
                    if dispatch.start_time >= _to_dt(start_to):
                        return False
            if _filter.HasField("end_time_interval"):
                if _filter.end_time_interval.HasField("start_time"):
                    end_from = _filter.end_time_interval.start_time
                    if dispatch.duration and (
                        dispatch.start_time + dispatch.duration < _to_dt(end_from)
                    ):
                        return False
                if _filter.end_time_interval.HasField("end_time"):
                    end_to = _filter.end_time_interval.end_time
                    if (
                        dispatch.duration
                        and dispatch.start_time + dispatch.duration >= _to_dt(end_to)
                    ):
                        return False
            if _filter.HasField("is_active"):
                if dispatch.active != _filter.is_active:
                    return False
            if _filter.HasField("is_dry_run"):
                if dispatch.dry_run != _filter.is_dry_run:
                    return False

            if len(_filter.dispatch_ids) > 0 and dispatch.id not in map(
                DispatchId, _filter.dispatch_ids
            ):
                return False

            if not FakeService._matches_query(_filter, dispatch):
                return False

        return True

    @staticmethod
    def _matches_query(filter_: DispatchFilter, dispatch: Dispatch) -> bool:
        """Check if a dispatch matches the query."""
        # Two cases:
        #  - query starts with # and is interpretable as int: filter by id
        #  - otherwise: filter by exact match in 'type' field
        # Multiple queries use OR logic - dispatch must match at least one
        if len(filter_.queries) > 0:
            matches_any_query = False
            for query in filter_.queries:
                if query.startswith("#"):
                    try:
                        int_id = int(query[1:])
                    except ValueError:
                        # not an int, interpret as exact type match (without the #)
                        if query[1:] == dispatch.type:
                            matches_any_query = True
                            break
                    else:
                        query_id = DispatchId(int_id)
                        if dispatch.id == query_id:
                            matches_any_query = True
                            break
                elif query == dispatch.type:
                    matches_any_query = True
                    break

            if not matches_any_query:
                return False

        return True

    async def CreateMicrogridDispatch(
        self,
        request: PBDispatchCreateRequest,
        timeout: int = 5,  # pylint: disable=unused-argument
    ) -> CreateMicrogridDispatchResponse:
        """Create a new dispatch."""
        microgrid_id = MicrogridId(request.microgrid_id)
        self._last_id = DispatchId(int(self._last_id) + 1)

        new_dispatch = _dispatch_from_request(
            DispatchCreateRequest.from_protobuf(request),
            self._last_id,
            create_time=datetime.now(tz=timezone.utc),
            update_time=datetime.now(tz=timezone.utc),
        )

        # implicitly create the list if it doesn't exist
        self.dispatches.setdefault(microgrid_id, []).append(new_dispatch)

        await self._stream_sender.send(
            self.StreamEvent(
                microgrid_id,
                DispatchEvent(dispatch=new_dispatch, event=Event.CREATED),
            )
        )

        return CreateMicrogridDispatchResponse(dispatch=new_dispatch.to_protobuf())

    async def UpdateMicrogridDispatch(
        self,
        request: UpdateMicrogridDispatchRequest,
        timeout: int = 5,  # pylint: disable=unused-argument
    ) -> UpdateMicrogridDispatchResponse:
        """Update a dispatch."""
        microgrid_id = MicrogridId(request.microgrid_id)
        grid_dispatches = self.dispatches.get(microgrid_id, [])
        index = next(
            (
                i
                for i, d in enumerate(grid_dispatches)
                if d.id == DispatchId(request.dispatch_id)
            ),
            None,
        )

        if index is None:
            error = grpc.RpcError()
            # pylint: disable=protected-access
            error._code = grpc.StatusCode.NOT_FOUND  # type: ignore
            error._details = "Dispatch not found"  # type: ignore
            # pylint: enable=protected-access
            raise error

        pb_dispatch = grid_dispatches[index].to_protobuf()

        # Go through the paths in the update mask and update the dispatch
        for path in request.update_mask.paths:
            split_path = path.split(".")

            match split_path[0]:
                # Fields that can be assigned directly
                case "is_active":
                    setattr(
                        pb_dispatch.data,
                        split_path[0],
                        getattr(request.update, split_path[0]),
                    )
                # Duration needs extra handling for clearing
                case "duration":
                    if request.update.HasField("duration"):
                        pb_dispatch.data.duration = request.update.duration
                    else:
                        pb_dispatch.data.ClearField("duration")
                # Fields that need to be copied
                case "start_time" | "target" | "payload":
                    getattr(pb_dispatch.data, split_path[0]).CopyFrom(
                        getattr(request.update, split_path[0])
                    )
                case "recurrence":
                    match split_path[1]:
                        case "end_criteria":
                            pb_dispatch.data.recurrence.end_criteria.CopyFrom(
                                request.update.recurrence.end_criteria
                            )
                        case "freq" | "interval":
                            setattr(
                                pb_dispatch.data.recurrence,
                                split_path[1],
                                getattr(request.update.recurrence, split_path[1]),
                            )
                        # Fields of type list that need to be copied
                        case (
                            "byminutes"
                            | "byhours"
                            | "byweekdays"
                            | "bymonthdays"
                            | "bymonths"
                        ):
                            getattr(pb_dispatch.data.recurrence, split_path[1])[:] = (
                                getattr(request.update.recurrence, split_path[1])[:]
                            )

        dispatch = Dispatch.from_protobuf(pb_dispatch)
        dispatch = replace(
            dispatch,
            update_time=datetime.now(tz=timezone.utc),
        )

        grid_dispatches[index] = dispatch

        await self._stream_sender.send(
            self.StreamEvent(
                microgrid_id,
                DispatchEvent(dispatch=dispatch, event=Event.UPDATED),
            )
        )

        return UpdateMicrogridDispatchResponse(dispatch=dispatch.to_protobuf())

    async def GetMicrogridDispatch(
        self,
        request: GetMicrogridDispatchRequest,
        timeout: int = 5,  # pylint: disable=unused-argument
    ) -> GetMicrogridDispatchResponse:
        """Get a single dispatch."""
        microgrid_id = MicrogridId(request.microgrid_id)
        grid_dispatches = self.dispatches.get(microgrid_id, [])
        dispatch = next(
            (d for d in grid_dispatches if d.id == DispatchId(request.dispatch_id)),
            None,
        )

        if dispatch is None:
            error = grpc.RpcError()
            # pylint: disable=protected-access
            error._code = grpc.StatusCode.NOT_FOUND  # type: ignore
            error._details = "Dispatch not found"  # type: ignore
            # pylint: enable=protected-access
            raise error

        return GetMicrogridDispatchResponse(dispatch=dispatch.to_protobuf())

    async def DeleteMicrogridDispatch(
        self,
        request: DeleteMicrogridDispatchRequest,
        timeout: int = 5,  # pylint: disable=unused-argument
    ) -> Empty:
        """Delete a given dispatch."""
        microgrid_id = MicrogridId(request.microgrid_id)
        grid_dispatches = self.dispatches.get(microgrid_id, [])

        dispatch_to_delete = next(
            (d for d in grid_dispatches if d.id == DispatchId(request.dispatch_id)),
            None,
        )

        if dispatch_to_delete is None:
            error = grpc.RpcError()
            # pylint: disable=protected-access
            error._code = grpc.StatusCode.NOT_FOUND  # type: ignore
            error._details = "Dispatch not found"  # type: ignore
            # pylint: enable=protected-access
            raise error

        grid_dispatches.remove(dispatch_to_delete)

        await self._stream_sender.send(
            self.StreamEvent(
                microgrid_id,
                DispatchEvent(
                    dispatch=dispatch_to_delete,
                    event=Event.DELETED,
                ),
            )
        )

        return Empty()

    # pylint: enable=invalid-name


def _dispatch_from_request(
    _request: DispatchCreateRequest,
    _id: DispatchId,
    create_time: datetime,
    update_time: datetime,
) -> Dispatch:
    """Initialize a Dispatch object from a request.

    Args:
        _request: The dispatch create request.
        _id: The unique identifier for the dispatch.
        create_time: The creation time of the dispatch in UTC.
        update_time: The last update time of the dispatch in UTC.

    Returns:
        The initialized dispatch.
    """
    params = _request.__dict__
    params.pop("microgrid_id")

    if _request.start_time == "NOW":
        params["start_time"] = datetime.now(tz=timezone.utc)

    return Dispatch(
        id=_id,
        create_time=create_time,
        update_time=update_time,
        **params,
    )
