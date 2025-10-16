from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from remotivelabs.broker.recording_session.offset import PlaybackOffset
from remotivelabs.broker.recording_session.repeat import PlaybackRepeat


@dataclass
class RecordingSessionPlaybackStatus:
    path: str
    mode: PlaybackMode
    offset: PlaybackOffset
    repeat: PlaybackRepeat | None = None


class RecordingSessionPlaybackError(Exception):
    pass


class PlaybackMode(Enum):
    PLAYBACK_PLAYING = 0
    """Playing a file."""
    PLAYBACK_PAUSED = 1
    """Playback is paused."""
    PLAYBACK_CLOSED = 2
    """Playback is closed."""
