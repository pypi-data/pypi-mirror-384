
#!/usr/bin/env python3
"""
SpeakUB - A modern terminal EPUB reader with TTS support.
"""

__version__ = "1.1.9"
__author__ = "SpeakUB Team"
__email__ = "team@speakub.com"
__description__ = "A rich terminal EPUB reader with TTS support"

from speakub.core.chapter_manager import ChapterManager
from speakub.core.content_renderer import ContentRenderer
from speakub.core.epub_parser import EPUBParser
from speakub.core.progress_tracker import ProgressTracker

# TTS integration is always available, but TTS functionality
# depends on edge_tts
from speakub.tts.integration import TTSIntegration  # noqa: F401

# Optional TTS imports
try:
    # Check for both the module and its core dependency
    import edge_tts  # noqa: F401

    from speakub.tts.edge_tts_provider import EdgeTTSProvider  # noqa: F401
    from speakub.tts.engine import TTSEngine  # noqa: F401

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "EPUBParser",
    "ContentRenderer",
    "ChapterManager",
    "ProgressTracker",
    "TTSIntegration",
    "TTS_AVAILABLE",
]

if TTS_AVAILABLE:
    __all__.extend(["TTSEngine", "EdgeTTSProvider"])
