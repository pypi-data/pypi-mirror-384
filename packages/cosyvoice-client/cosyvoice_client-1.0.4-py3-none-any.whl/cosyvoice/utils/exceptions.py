"""Custom exception definitions

Defines all custom exception types used in the SDK.
"""

from typing import Any


class CosyVoiceError(Exception):
    """CosyVoice SDK base exception"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConnectionError(CosyVoiceError):
    """Connection related exception"""
    pass


class InvalidStateError(CosyVoiceError):
    """Invalid state exception

    Raised when client performs operations in incorrect state.
    """
    pass


class SpeakerError(CosyVoiceError):
    """Speaker management related exception"""
    pass


class SynthesisError(CosyVoiceError):
    """Speech synthesis related exception"""
    pass


class ValidationError(CosyVoiceError):
    """Parameter validation exception"""
    pass


class ConfigurationError(CosyVoiceError):
    """Configuration error exception"""
    pass


class TimeoutError(CosyVoiceError):
    """Timeout exception"""
    pass


class WebSocketError(ConnectionError):
    """WebSocket connection exception"""
    pass


class AuthenticationError(CosyVoiceError):
    """Authentication exception"""
    pass


class RateLimitError(CosyVoiceError):
    """Rate limit exception"""
    pass


class ServiceUnavailableError(CosyVoiceError):
    """Service unavailable exception"""
    pass
