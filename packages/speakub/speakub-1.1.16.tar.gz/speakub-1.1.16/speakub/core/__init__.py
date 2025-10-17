
"""
Core functionality for SpeakUB.
"""


class SpeakUBError(Exception):
    """Base exception for SpeakUB errors."""


class NetworkError(SpeakUBError):
    """Network-related errors."""


class TTSError(SpeakUBError):
    """TTS-related errors."""


class ParseError(SpeakUBError):
    """Parsing-related errors."""


class ConfigurationError(SpeakUBError):
    """Configuration-related errors."""


class FileSizeError(SpeakUBError):
    """File size-related errors."""


class SecurityError(SpeakUBError):
    """Security-related errors."""
