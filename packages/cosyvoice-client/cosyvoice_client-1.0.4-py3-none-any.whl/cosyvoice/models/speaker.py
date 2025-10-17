"""Speaker management related data models"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateSpeakerRequest(BaseModel):
    """Create speaker request"""
    prompt_text: str = Field(
        default="希望你以后能够做的比我还好呦。",
        min_length=1,
        max_length=500,
        description="Reference text"
    )
    zero_shot_spk_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Speaker ID, will be auto-generated if not provided"
    )
    prompt_audio_path: str = Field(..., description="Reference audio file URL")

    @field_validator('zero_shot_spk_id')
    @classmethod
    def validate_speaker_id(cls, v: str | None) -> str | None:
        """Validate speaker ID format"""
        if v is None:
            return v
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Speaker ID can only contain letters, numbers, underscores and hyphens")
        return v

    @field_validator('prompt_audio_path')
    @classmethod
    def validate_audio_url(cls, v: str) -> str:
        """Validate audio URL - only supports URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("prompt_audio_path only supports HTTP/HTTPS URLs")
        return v


class UpdateSpeakerRequest(BaseModel):
    """Update speaker request"""
    prompt_text: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="New reference text"
    )
    prompt_audio_path: str | None = Field(
        default=None,
        description="New reference audio file URL"
    )

    @field_validator('prompt_audio_path')
    @classmethod
    def validate_audio_url(cls, v: str | None) -> str | None:
        """Validate audio URL"""
        if v is None:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError("prompt_audio_path only supports HTTP/HTTPS URLs")
        return v


class SpeakerResponse(BaseModel):
    """Speaker operation response - consistent with server API"""
    is_success: bool = Field(..., description="Whether the operation was successful")
    error: dict[str, Any] | None = Field(None, description="Error information")
    speaker_info: dict[str, Any] | None = Field(None, description="Speaker information")
    request_id: str | None = Field(None, description="Request ID")


class SpeakerInfo(BaseModel):
    """Speaker information - matches server response fields"""
    zero_shot_spk_id: str = Field(..., description="Speaker ID")
    prompt_text: str = Field(..., description="Reference text")
    created_at: str | None = Field(None, description="Creation time (ISO format)")
    audio_url: str | None = Field(None, description="Audio URL")

