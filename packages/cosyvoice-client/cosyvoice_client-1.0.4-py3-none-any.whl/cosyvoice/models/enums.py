"""Enumeration definitions

Defines all enumeration types used in the SDK.
"""

from enum import Enum


class AudioFormat(str, Enum):
    """Audio output format"""
    WAV = "wav"
    MP3 = "mp3"
    PCM = "pcm"


class SynthesisMode(str, Enum):
    """Speech synthesis mode"""
    ZERO_SHOT = "zero_shot"
    """Zero-shot synthesis mode, using custom voice"""

    SFT = "sft"
    """SFT mode, using pre-trained voice"""

    CROSS_LINGUAL = "cross_lingual"
    """Cross-lingual synthesis mode"""

    INSTRUCT = "instruct2"
    """Instruction mode, supports natural language control"""


class ClientState(str, Enum):
    """Client connection state"""
    DISCONNECTED = "disconnected"
    """Disconnected state"""

    CONNECTING = "connecting"
    """Connecting"""

    CONNECTED = "connected"
    """Connected, but no active session"""

    SESSION_ACTIVE = "session_active"
    """Session created"""

    SYNTHESIZING = "synthesizing"
    """Performing speech synthesis"""

    CLOSING = "closing"
    """Closing connection"""

    ERROR = "error"
    """Error state"""


class MessageType(str, Enum):
    """WebSocket message type"""
    # Messages sent by client
    CONNECT_REQUEST = "CONNECT_REQUEST"
    SESSION_REQUEST = "SESSION_REQUEST"
    SYNTHESIS_START = "SYNTHESIS_START"
    TEXT_REQUEST = "TEXT_REQUEST"
    SYNTHESIS_END = "SYNTHESIS_END"
    SESSION_END = "SESSION_END"

    # Messages responded by server
    CONNECT_RESPONSE = "CONNECT_RESPONSE"
    SESSION_RESPONSE = "SESSION_RESPONSE"
    SYNTHESIS_START_ACK = "SYNTHESIS_START_ACK"
    TEXT_ACCEPTED = "TEXT_ACCEPTED"
    AUDIO_RESPONSE = "AUDIO_RESPONSE"
    AUDIO_COMPLETE = "AUDIO_COMPLETE"
    SYNTHESIS_END_ACK = "SYNTHESIS_END_ACK"
    SESSION_END_ACK = "SESSION_END_ACK"
    ERROR_RESPONSE = "ERROR_RESPONSE"

