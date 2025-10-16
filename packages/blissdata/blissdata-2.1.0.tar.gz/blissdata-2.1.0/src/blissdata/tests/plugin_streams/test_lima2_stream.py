# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.

"""Unit test suite for Lima2 stream and view (streams/lima2.py)."""

from unittest.mock import Mock, call
from uuid import uuid1

import pytest
import numpy as np
from blissdata.lima.image_utils import ImageData
from blissdata.redis_engine.event_stream import EventStream
from blissdata.streams.lima2.stream import get_frame, Lima2View, Lima2Stream
from blissdata.redis_engine.exceptions import IndexNotYetThereError


def test_lima2_get_frame():
    services = Mock()
    uuid = str(uuid1())
    frm = get_frame(services=services, acq_uuid=uuid, source="cafe", frame_idx=123)
    services.pipeline.get_frame.assert_called_with(
        frame_idx=123, source="cafe", uuid=uuid
    )
    assert type(frm) is ImageData


def test_lima2_view():
    services = Mock()
    uuid = str(uuid1())
    view = Lima2View(
        services=services,
        acq_uuid=uuid,
        source="cafe",
        start=0,
        stop=42,
    )
    assert len(view) == 42
    assert view.index == 0

    frames = view.get_data()
    assert len(frames) == len(view)

    services.pipeline.get_frame.assert_has_calls(
        [call(uuid=uuid, source="cafe", frame_idx=i) for i in range(42)]
    )


def test_lima2_protocol(data_store):
    uuid = str(uuid1())

    stream_def = Lima2Stream.make_definition(
        name="device:cafe",
        source_name="cafe",
        conductor_hostname="www.lima2.org",
        conductor_port=12345,
        acq_uuid=uuid,
        master_file=None,
        dtype=np.float128,  # fat pixels >:)
        shape=(4, 1024, 512),
    )
    model = data_store._stream_model(
        encoding=stream_def.encoder.info(), info=stream_def.info
    )
    model.info["protocol_version"] = 1  # hack the protocol number
    event_stream = EventStream.create(data_store, stream_def.name, model)

    with pytest.raises(RuntimeError):
        _ = Lima2Stream(event_stream=event_stream)


def test_lima2_stream(data_store, monkeypatch):
    uuid = str(uuid1())

    stream_def = Lima2Stream.make_definition(
        name="device:cafe",
        source_name="cafe",
        conductor_hostname="www.lima2.org",
        conductor_port=12345,
        acq_uuid=uuid,
        master_file=None,
        dtype=np.float128,  # fat pixels >:)
        shape=(4, 1024, 512),
    )
    model = data_store._stream_model(
        encoding=stream_def.encoder.info(), info=stream_def.info
    )

    event_stream = EventStream.create(data_store, stream_def.name, model)
    stream = Lima2Stream(event_stream=event_stream)

    assert stream.plugin == "lima2"
    assert stream.shape == stream_def.info["shape"]

    # Feed the event stream
    event_stream.send(np.uint32(42))
    event_stream.join()
    assert len(stream) == 42

    event_stream.send(np.uint32(123))
    event_stream.join()
    assert len(stream) == 123

    mock_get_frame = Mock()
    monkeypatch.setattr("blissdata.streams.lima2.stream.get_frame", mock_get_frame)

    # Indexing
    _ = stream[0]
    mock_get_frame.assert_called_with(
        services=stream._services,
        acq_uuid=uuid,
        source="cafe",
        frame_idx=0,
    )

    with pytest.raises(IndexNotYetThereError):
        _ = stream[-1]

    # Slicing
    _ = stream[:3]
    assert mock_get_frame.mock_calls[-3:] == [
        call(services=stream._services, acq_uuid=uuid, source="cafe", frame_idx=0),
        call(services=stream._services, acq_uuid=uuid, source="cafe", frame_idx=1),
        call(services=stream._services, acq_uuid=uuid, source="cafe", frame_idx=2),
    ]

    with pytest.raises(IndexNotYetThereError):
        _ = stream[-2:]

    with pytest.raises(IndexNotYetThereError):
        _ = stream[:-2]

    event_stream.seal()
    event_stream.join()

    # Now slicing/indexing from end is ok
    _ = stream[-2:]
    assert mock_get_frame.mock_calls[-2:] == [
        call(
            services=stream._services,
            acq_uuid=uuid,
            source="cafe",
            frame_idx=123 - 2,
        ),
        call(
            services=stream._services,
            acq_uuid=uuid,
            source="cafe",
            frame_idx=123 - 1,
        ),
    ]

    _ = stream[-3]
    assert mock_get_frame.mock_calls[-1] == call(
        services=stream._services,
        acq_uuid=uuid,
        source="cafe",
        frame_idx=123 - 3,
    )

    _ = stream[:]
    assert mock_get_frame.mock_calls[-123:] == [
        call(services=stream._services, acq_uuid=uuid, source="cafe", frame_idx=i)
        for i in range(123)
    ]
