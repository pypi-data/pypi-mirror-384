from __future__ import annotations

from remotivelabs.broker._generated import recordingsession_api_pb2 as recordingsession__api__pb2


def open_to_grpc(path: str, force: bool) -> recordingsession__api__pb2.RecordingSessionOpenCommand:
    return recordingsession__api__pb2.RecordingSessionOpenCommand(path=path, force=force)


def close_to_grpc(path: str) -> recordingsession__api__pb2.RecordingSessionCloseCommand:
    return recordingsession__api__pb2.RecordingSessionCloseCommand(
        path=path,
    )


def set_repeat_to_grpc(
    path: str, start_offset: int | None, end_offset: int | None
) -> recordingsession__api__pb2.RecordingSessionCloseCommand:
    return recordingsession__api__pb2.RecordingSessionRepeatCommand(path=path, startOffset=start_offset, endOffset=end_offset)


def play_to_grpc(path: str, offset: int | None) -> recordingsession__api__pb2.RecordingSessionPlayCommand:
    return recordingsession__api__pb2.RecordingSessionPlayCommand(
        path=path,
        offset=offset,
    )


def pause_to_grpc(path: str, offset: int | None) -> recordingsession__api__pb2.RecordingSessionPauseCommand:
    return recordingsession__api__pb2.RecordingSessionPauseCommand(
        path=path,
        offset=offset,
    )


def seek_to_grpc(path: str, offset: int) -> recordingsession__api__pb2.RecordingSessionSeekCommand:
    return recordingsession__api__pb2.RecordingSessionSeekCommand(
        path=path,
        offset=offset,
    )
