from dataclasses import dataclass


@dataclass
class PlaybackOffset:
    """Current offset in micro seconds."""

    offset: int = 0
