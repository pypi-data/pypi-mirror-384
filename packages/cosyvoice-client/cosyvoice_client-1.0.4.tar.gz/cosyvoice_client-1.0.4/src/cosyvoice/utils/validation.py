"""Parameter validation utilities

Provides various parameter validation functions.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

from .exceptions import ValidationError


def validate_url(url: str) -> bool:
    """Validate URL format

    Args:
        url: URL to validate

    Returns:
        True if URL format is correct

    Raises:
        ValidationError: URL format is incorrect
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError(f"Invalid URL format: {url}")

        if result.scheme not in ('http', 'https', 'ws', 'wss'):
            raise ValidationError(f"Unsupported URL protocol: {result.scheme}")

        return True
    except Exception as e:
        raise ValidationError(f"URL validation failed: {e!s}") from e


def validate_file_path(file_path: str | Path) -> bool:
    """Validate file path

    Args:
        file_path: File path to validate

    Returns:
        True if file exists and is readable

    Raises:
        ValidationError: File does not exist or is not readable
    """
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    if not path.stat().st_size > 0:
        raise ValidationError(f"File is empty: {file_path}")

    return True


def validate_audio_format(file_path: str | Path) -> bool:
    """Validate audio file format

    Args:
        file_path: Audio file path

    Returns:
        True if supported audio format

    Raises:
        ValidationError: Unsupported audio format
    """
    path = Path(file_path)

    # Supported audio formats
    supported_formats = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg'}

    if path.suffix.lower() not in supported_formats:
        raise ValidationError(
            f"Unsupported audio format: {path.suffix}. "
            f"Supported formats: {', '.join(supported_formats)}"
        )

    return True


def validate_speaker_id(speaker_id: str) -> bool:
    """Validate speaker ID format

    Args:
        speaker_id: Speaker ID

    Returns:
        True if format is correct

    Raises:
        ValidationError: Format is incorrect
    """
    if not speaker_id:
        raise ValidationError("Speaker ID cannot be empty")

    if len(speaker_id) > 100:
        raise ValidationError("Speaker ID length cannot exceed 100 characters")

    # Only allow letters, numbers, underscores and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', speaker_id):
        raise ValidationError("Speaker ID can only contain letters, numbers, underscores and hyphens")

    return True


def validate_text_content(text: str) -> bool:
    """Validate text content

    Args:
        text: Text to validate

    Returns:
        True if text is valid

    Raises:
        ValidationError: Text is invalid
    """
    if not text:
        raise ValidationError("Text content cannot be empty")

    if len(text.strip()) == 0:
        raise ValidationError("Text content cannot contain only whitespace")

    if len(text) > 5000:
        raise ValidationError("Text length cannot exceed 5000 characters")

    return True


def validate_speed(speed: float) -> bool:
    """Validate speech speed parameter

    Args:
        speed: Speech speed multiplier

    Returns:
        True if speed is valid

    Raises:
        ValidationError: Speed is invalid
    """
    if not isinstance(speed, int | float):
        raise ValidationError("Speed must be a number")

    if speed <= 0:
        raise ValidationError("Speed must be greater than 0")

    if speed > 3.0:
        raise ValidationError("Speed cannot exceed 3.0x")

    return True
