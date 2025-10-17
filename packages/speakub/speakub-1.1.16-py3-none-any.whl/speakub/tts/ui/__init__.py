
"""TTS UI components for SpeakUB."""

from .network import NetworkManager
from .playlist import prepare_tts_playlist, tts_load_next_chapter
from .runners import (
    find_and_play_next_chapter_worker,
    tts_pre_synthesis_worker,
    tts_runner_parallel,
    tts_runner_serial,
)

__all__ = [
    "NetworkManager",
    "prepare_tts_playlist",
    "tts_load_next_chapter",
    "find_and_play_next_chapter_worker",
    "tts_pre_synthesis_worker",
    "tts_runner_parallel",
    "tts_runner_serial",
]
