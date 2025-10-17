"""Speech synthesis related data models"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import AudioFormat, SynthesisMode


class SynthesisConfig(BaseModel):
    """Speech synthesis configuration

    Defines all parameters for speech synthesis.
    """
    speaker_id: str = Field(..., description="Speaker ID, references created speaker")
    mode: SynthesisMode = Field(default=SynthesisMode.ZERO_SHOT, description="Synthesis mode")
    speed: float = Field(default=1.0, ge=0.5, le=3.0, description="Speech speed multiplier")
    output_format: AudioFormat = Field(default=AudioFormat.WAV, description="Output audio format")
    sample_rate: int | None = Field(default=None, description="Output sample rate (Hz)")
    instruct_text: str | None = Field(default=None, description="Instruction text (instruct mode only)")
    bit_rate: int | None = Field(default=192000, description="Bit rate (MP3 format only)")
    compression_level: int | None = Field(default=2, ge=0, le=9, description="Compression level")

    @field_validator('sample_rate')
    @classmethod
    def validate_sample_rate(cls, v: int | None) -> int | None:
        """Validate sample rate"""
        if v is not None and v not in [8000, 16000, 22050, 24000, 44100, 48000]:
            raise ValueError(f"Unsupported sample rate: {v}")
        return v

    @model_validator(mode='after')
    def validate_instruct_mode(self) -> 'SynthesisConfig':
        """Validate instruct mode configuration"""
        if self.mode == SynthesisMode.INSTRUCT and not self.instruct_text:
            raise ValueError("instruct_text is required in instruct mode")
        return self

    model_config = {
        "frozen": True,  # Immutable configuration
        "use_enum_values": True,
    }


class SynthesisResult(BaseModel):
    """Speech synthesis result

    Represents synthesis result of a single audio chunk.
    """
    audio_data: bytes = Field(..., description="Audio data bytes")
    session_id: str = Field(..., description="Session ID")
    text_index: int = Field(..., ge=0, description="Text sequence index")
    chunk_index: int = Field(..., ge=0, description="Audio chunk index")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Timestamp")

    model_config = {
        "arbitrary_types_allowed": True,
    }


# Simple metrics for debugging - can be logged but not as complex statistics
def calculate_rtf(synthesis_time: float, audio_duration: float) -> float:
    """Calculate Real-Time Factor (RTF): synthesis_time / audio_duration

    RTF < 1.0 means faster than real-time synthesis
    RTF > 1.0 means slower than real-time synthesis
    """
    return synthesis_time / audio_duration if audio_duration > 0 else 0.0


def calculate_fftb(first_chunk_time: float) -> float:
    """Calculate First Frame Time to Bytes (FFTB) - first chunk latency in milliseconds

    Lower values indicate better responsiveness
    """
    return first_chunk_time * 1000  # Convert to milliseconds
