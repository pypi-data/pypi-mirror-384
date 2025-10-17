"""CosyVoice Python SDK

Asynchronous streaming TTS client, designed specifically for CosyVoice service.

Key Features:
- Async-first design
- Real-time streaming TTS
- Event-driven audio processing
- Complete speaker management functionality
- Type-safe API
"""

from .client import StreamClient, connect_client, create_client
from .models.enums import AudioFormat, ClientState, SynthesisMode
from .models.speaker import CreateSpeakerRequest, SpeakerInfo
from .models.synthesis import SynthesisConfig
from .speaker.manager import SpeakerManager
from .utils.exceptions import (
    ConfigurationError,
    ConnectionError,
    CosyVoiceError,
    InvalidStateError,
    SpeakerError,
    SynthesisError,
    ValidationError,
)

__version__ = "1.0.4"
__author__ = "CosyVoice Team"
__email__ = "noreply@cosyvoice.com"
__license__ = "MIT"

__all__ = [
    "AudioFormat",
    "ClientState",
    "ConfigurationError",
    "ConnectionError",
    "CosyVoiceError",
    "CreateSpeakerRequest",
    "InvalidStateError",
    "SpeakerError",
    "SpeakerInfo",
    "SpeakerManager",
    "StreamClient",
    "SynthesisConfig",
    "SynthesisError",
    "SynthesisMode",
    "ValidationError",
    "connect_client",
    "create_client",
]
