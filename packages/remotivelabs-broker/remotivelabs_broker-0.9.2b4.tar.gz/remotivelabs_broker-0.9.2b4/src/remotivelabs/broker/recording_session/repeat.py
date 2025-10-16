from dataclasses import dataclass


@dataclass
class PlaybackRepeat:
    """Playback repeat settings."""

    start_offset: int = 0
    """Current cycle start in micro seconds."""
    end_offset: int = 0
    """Current cycle end in micro seconds."""
