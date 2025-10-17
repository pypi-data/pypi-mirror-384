
#!/usr/bin/env python3
"""
Unified exception handling for SpeakUB.
"""

import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SpeakUBException(Exception):
    """Base exception with logging support"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.details = details or {}
        self.timestamp = time.time()
        logger.error(f"{self.__class__.__name__}: {message}",
                     extra={"details": self.details})


class NetworkException(SpeakUBException):
    """Network-related errors"""
    pass


class ParsingException(SpeakUBException):
    """Parsing-related errors"""
    pass


class ConfigurationException(SpeakUBException):
    """Configuration-related errors"""
    pass


class SecurityException(SpeakUBException):
    """Security-related errors"""
    pass


class TTSException(SpeakUBException):
    """TTS-related errors"""
    pass


class CacheException(SpeakUBException):
    """Cache-related errors"""
    pass
