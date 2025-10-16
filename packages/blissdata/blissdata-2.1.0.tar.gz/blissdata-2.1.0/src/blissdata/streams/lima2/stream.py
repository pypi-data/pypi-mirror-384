# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.

import logging
from collections.abc import Sequence

import lima2.client.services as l2s
import numpy as np
from lima2.common.devencoded.sparse_frame import SparseFrame
from numpy.typing import DTypeLike

from blissdata.lima.image_utils import ImageData
from blissdata.redis_engine.encoding.numeric import NumericStreamEncoder
from blissdata.redis_engine.exceptions import (
    IndexNoMoreThereError,
    IndexNotYetThereError,
)
from blissdata.streams.base import (
    BaseStream,
    BaseView,
    EndOfStream,
    EventRange,
    EventStream,
    Stream,
    StreamDefinition,
)

_logger = logging.getLogger(__name__)


def get_frame(
    services: l2s.ConductorServices,
    acq_uuid: str,
    source: str,
    frame_idx: int,
) -> ImageData:
    frm = services.pipeline.get_frame(frame_idx=frame_idx, source=source, uuid=acq_uuid)

    if isinstance(frm, SparseFrame):
        frm = frm.densify()

    return ImageData(array=frm.data, frame_id=frm.idx, acq_tag=None)


class Lima2View(BaseView):
    def __init__(
        self,
        services: l2s.ConductorServices,
        acq_uuid: str,
        source: str,
        start: int,
        stop: int,
    ) -> None:
        self._services = services
        """Lima2 client services."""
        self._acq_uuid = acq_uuid
        """Lima2 acquisition id."""
        self._source = source
        """Frame source name."""
        self._idx_range = range(start, stop)
        """Range of absolute frame indices accessible via this view."""

    @property
    def index(self) -> int:
        return self._idx_range.start

    def __len__(self) -> int:
        return len(self._idx_range)

    def get_data(
        self, start: int | None = None, stop: int | None = None
    ) -> list[ImageData]:
        try:
            return [
                get_frame(
                    services=self._services,
                    acq_uuid=self._acq_uuid,
                    source=self._source,
                    frame_idx=idx,
                )
                for idx in self._idx_range[start:stop]
            ]
        except RuntimeError as e:
            raise IndexNoMoreThereError(
                f"Can't fetch {self._source} {self._idx_range[start:stop].start} "
                f"to {self._idx_range[start:stop].stop}: {e}"
            ) from e

    def get_latest(self) -> ImageData:
        """
        Access the most up to date frame, possibly going beyond this view's
        index range.
        """
        return get_frame(
            services=self._services,
            acq_uuid=self._acq_uuid,
            source=self._source,
            frame_idx=-1,
        )


class Lima2Stream(BaseStream):
    """Stream of Lima2 frames.

    Frames don't actually transit inside the stream. The stream length can be
    queried to determine the number of accessible frames.

    Indexing or slicing the stream attempts to fetch frames directly from the
    Lima2 backend.
    """

    PROTOCOL_VERSION = 2

    def __init__(self, event_stream: EventStream) -> None:
        BaseStream.__init__(self, event_stream)

        _logger.debug(f"Instantiate Lima2Stream with {event_stream.info=}")

        if event_stream.info["protocol_version"] != Lima2Stream.PROTOCOL_VERSION:
            raise RuntimeError(
                f"Lima2 protocol version mismatch "
                f"(expected {Lima2Stream.PROTOCOL_VERSION}, "
                f"got {event_stream.info['protocol_version']})"
            )

        self._dtype = np.dtype(event_stream.info["dtype"])
        self._shape = tuple(event_stream.info["shape"])
        self._acq_uuid = str(event_stream.info["acq_uuid"])
        self._source = str(event_stream.info["source_name"])

        self._services = l2s.init(
            hostname=str(event_stream.info["conductor_hostname"]),
            port=int(event_stream.info["conductor_port"]),
        )
        """Lima2 client session."""

        self._length = 0
        """Current number of accessible frames."""

        self._cursor = Stream(event_stream).cursor()

    @property
    def kind(self):
        return "array"

    @staticmethod
    def make_definition(
        name: str,
        source_name: str,
        conductor_hostname: str,
        conductor_port: int,
        acq_uuid: str,
        master_file: tuple[str, str] | None,
        dtype: DTypeLike,
        shape: Sequence,
    ) -> StreamDefinition:
        info = {
            "plugin": "lima2",
            "dtype": np.dtype(dtype).name,
            "shape": shape,
            "protocol_version": Lima2Stream.PROTOCOL_VERSION,
            "acq_uuid": acq_uuid,
            "source_name": source_name,
            "conductor_hostname": conductor_hostname,
            "conductor_port": conductor_port,
            "master_file": master_file,
        }

        return StreamDefinition(name, info, NumericStreamEncoder(np.uint32))

    @property
    def plugin(self) -> str:
        return "lima2"

    @property
    def dtype(self) -> np.dtype:
        return self._dtype

    @property
    def shape(self) -> tuple[int, ...]:
        return self._shape

    def __len__(self) -> int:
        try:
            view = self._cursor.read(block=False, last_only=True)
        except EndOfStream:
            view = None

        if view is not None:
            last_status = view.get_data()[0]
            self._length = int(last_status)
        return self._length

    def __getitem__(self, key: int | slice) -> ImageData | list[ImageData]:
        idx_range = range(len(self))
        if type(key) is int:
            if key < 0 and not self.is_sealed():
                raise IndexNotYetThereError(
                    "Can't index from end of stream until it is sealed"
                )
            return get_frame(
                services=self._services,
                acq_uuid=self._acq_uuid,
                source=self._source,
                frame_idx=idx_range[key],
            )
        elif type(key) is slice:
            if not self.is_sealed() and ((key.start or 0) < 0 or (key.stop or 0) < 0):
                raise IndexNotYetThereError(
                    "Can't slice from end of stream until it is sealed"
                )

            return [
                get_frame(
                    services=self._services,
                    acq_uuid=self._acq_uuid,
                    source=self._source,
                    frame_idx=idx,
                )
                for idx in idx_range[key]
            ]
        else:
            raise TypeError(f"{type(key)}")

    def _need_last_only(self, last_only: bool) -> bool:
        # Lima2 event stream represents current progress
        # -> only the latest one is relevant.
        return True

    def _build_view_from_events(
        self, index: int, events: EventRange, last_only: bool
    ) -> Lima2View:
        """
        Build a Lima2View to access a slice of frames which starts at `index`,
        and ends at the most recent frame according to `events`.
        """
        _logger.debug(f"{self.name}: {index=} -> {events=}")

        # events.data[-1] corresponds to the current number of contiguous frames
        # accessible from the lima2 backend.
        stop_idx = events.data[-1]

        return Lima2View(
            services=self._services,
            acq_uuid=self._acq_uuid,
            source=self._source,
            start=index,
            stop=stop_idx,
        )
