"""Speaker management related data models

Re-exports speaker-related models from the models module.
"""

from ..models.speaker import (
    CreateSpeakerRequest,
    SpeakerInfo,
    SpeakerResponse,
    UpdateSpeakerRequest,
)

__all__ = [
    "CreateSpeakerRequest",
    "SpeakerInfo",
    "SpeakerResponse",
    "UpdateSpeakerRequest",
]
