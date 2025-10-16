from __future__ import annotations

from remotivelabs.broker._generated import recordingsession_api_pb2 as recordingsession__api__pb2
from remotivelabs.broker.recording_session.offset import PlaybackOffset
from remotivelabs.broker.recording_session.repeat import PlaybackRepeat
from remotivelabs.broker.recording_session.status import PlaybackMode, RecordingSessionPlaybackStatus


def status_from_grpc(
    status: recordingsession__api__pb2.RecordingSessionPlaybackStatus,
) -> RecordingSessionPlaybackStatus:
    return RecordingSessionPlaybackStatus(
        path=status.path,
        mode=PlaybackMode(status.mode),
        offset=PlaybackOffset(status.offset),
        repeat=PlaybackRepeat(
            start_offset=status.repeat.startOffset,
            end_offset=status.repeat.endOffset,
        )
        if status.HasField("repeat")
        else None,
    )
