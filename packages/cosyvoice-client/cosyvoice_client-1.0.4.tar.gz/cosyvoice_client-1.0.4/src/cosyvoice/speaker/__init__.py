"""Speaker management package

Provides speaker creation, query, update, and deletion management functions.
"""

from .manager import SpeakerManager
from .models import CreateSpeakerRequest, SpeakerInfo, UpdateSpeakerRequest

__all__ = [
    "CreateSpeakerRequest",
    "SpeakerInfo",
    "SpeakerManager",
    "UpdateSpeakerRequest",
]
