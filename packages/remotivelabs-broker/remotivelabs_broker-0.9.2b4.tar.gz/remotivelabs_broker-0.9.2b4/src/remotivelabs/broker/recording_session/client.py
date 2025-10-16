from __future__ import annotations

from typing import AsyncIterator

from grpc.aio import AioRpcError

from remotivelabs.broker._generated import common_pb2
from remotivelabs.broker._generated import recordingsession_api_pb2 as recordingsession__api__pb2
from remotivelabs.broker.client import BrokerClient
from remotivelabs.broker.conv.grpc_recording_session_command import (
    close_to_grpc,
    open_to_grpc,
    pause_to_grpc,
    play_to_grpc,
    seek_to_grpc,
    set_repeat_to_grpc,
)
from remotivelabs.broker.conv.grpc_recording_session_file import file_from_grpc
from remotivelabs.broker.conv.grpc_recording_session_status import status_from_grpc
from remotivelabs.broker.recording_session.file import File
from remotivelabs.broker.recording_session.status import RecordingSessionPlaybackError, RecordingSessionPlaybackStatus


class RecordingSessionClient(BrokerClient):
    """
    TODO: We probably dont want to inherit from BrokerClient, but rather use composition to hide functionality not relevant for recording
    session operations. However, this will do for now.
    """

    async def __aenter__(self) -> RecordingSessionClient:
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)

    async def list_recording_files(self, path: str | None = None) -> list[File]:
        """
        List recording files in a directory.

        Args:
            path: Optional path to the subdirectory containing the recording files.
        """
        res = await self._recording_session_service.ListRecordingFiles(recordingsession__api__pb2.FileListingRequest(path=path))
        return [file_from_grpc(file) for file in res.files]

    def playback_status(self) -> AsyncIterator[list[RecordingSessionPlaybackStatus]]:
        """
        Get continuous status of all open recording sessions.
        """
        stream = self._recording_session_service.PlaybackStatus(common_pb2.Empty())

        async def async_generator() -> AsyncIterator[list[RecordingSessionPlaybackStatus]]:
            async for statuses in stream:
                status_list: list[recordingsession__api__pb2.RecordingSessionPlaybackStatus] = statuses.items
                yield [status_from_grpc(status) for status in status_list]

        return async_generator()

    def get_session(self, path: str, force_reopen: bool = False) -> RecordingSession:
        """
        Return a RecordingSession for the given path.

        Args:
            path: The path to the recording session file.
            force_reopen: Whether to force close any existing session before opening.
        """
        return RecordingSession(self, path, force_reopen=force_reopen)


class RecordingSession:
    def __init__(self, client: RecordingSessionClient, path: str, force_reopen: bool = False):
        self._client = client
        self.path = path
        self._force_reopen = force_reopen

    async def __aenter__(self):
        await self.open(force_reopen=self._force_reopen)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def open(self, force_reopen: bool = False) -> RecordingSessionPlaybackStatus:
        """
        Open recording session for playback.
        If force_reopen is True, close any existing session before opening.

        Args:
            force_reopen: Whether to force close any existing session before opening.

        Raises:
            RecordingSessionPlaybackError: On failures to open the session.
        """
        grpc_command = open_to_grpc(self.path, force_reopen)
        try:
            res = await self._client._recording_session_service.PlaybackOpen(grpc_command)
            return status_from_grpc(res)
        except AioRpcError as e:
            raise RecordingSessionPlaybackError(e.details() or "Unknown error occurred")

    async def play(self, offset: int | None = None) -> RecordingSessionPlaybackStatus:
        """
        Start or continue playback of an open recording session.

        Args:
            offset: The offset in microseconds from which to start playback. If None, playback continues from the current position.

        Raises:
            RecordingSessionPlaybackError: On playback errors
        """
        grpc_command = play_to_grpc(self.path, offset)
        try:
            res = await self._client._recording_session_service.PlaybackPlay(grpc_command)
            return status_from_grpc(res)
        except AioRpcError as e:
            raise RecordingSessionPlaybackError(e.details() or "Unknown error occurred")

    async def pause(self, offset: int | None = None) -> RecordingSessionPlaybackStatus:
        """
        Pause playback of an open recording session.

        Args:
            offset: Target position in microseconds at where the playback cursor is put after pausing.

        Raises:
            RecordingSessionPlaybackError: On playback errors
        """
        grpc_command = pause_to_grpc(self.path, offset)
        try:
            res = await self._client._recording_session_service.PlaybackPause(grpc_command)
            return status_from_grpc(res)
        except AioRpcError as e:
            raise RecordingSessionPlaybackError(e.details() or "Unknown error occurred")

    async def seek(self, offset: int) -> RecordingSessionPlaybackStatus:
        """
        Move playback to a target offset within the currently open recording session.

        Args:
            offset: Target position in microseconds.

        Raises:
            RecordingSessionPlaybackError: On playback errors
        """
        grpc_command = seek_to_grpc(self.path, offset)
        try:
            res = await self._client._recording_session_service.PlaybackSeek(grpc_command)
            return status_from_grpc(res)
        except AioRpcError as e:
            raise RecordingSessionPlaybackError(e.details() or "Unknown error occurred")

    async def close(self) -> RecordingSessionPlaybackStatus:
        """
        Close an open recording session.
        """
        grpc_command = close_to_grpc(self.path)
        try:
            res = await self._client._recording_session_service.PlaybackClose(grpc_command)
            return status_from_grpc(res)
        except AioRpcError as e:
            raise RecordingSessionPlaybackError(e.details() or "Unknown error occurred")

    async def set_repeat(self, start_offset: int | None = None, end_offset: int | None = None) -> RecordingSessionPlaybackStatus:
        """
        Set repeat mode for the currently open recording session.

        Args:
            start_offset: Start offset in microseconds for the repeat segment. If None, repeat from the start of the recording.
            end_offset: End offset in microseconds for the repeat segment. If None, repeat until the end of the recording.
        """
        grpc_command = set_repeat_to_grpc(self.path, start_offset, end_offset)
        try:
            res = await self._client._recording_session_service.PlaybackRepeat(grpc_command)
            return status_from_grpc(res)
        except AioRpcError as e:
            raise RecordingSessionPlaybackError(e.details() or "Unknown error occurred")
