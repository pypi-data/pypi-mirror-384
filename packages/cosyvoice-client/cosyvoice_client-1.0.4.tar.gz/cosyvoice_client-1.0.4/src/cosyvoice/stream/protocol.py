"""WebSocket protocol handling

Implements WebSocket communication protocol with CosyVoice server.
"""

import json
from datetime import datetime
from typing import Any

from ..models.enums import MessageType
from ..utils.exceptions import ValidationError


class MessageBuilder:
    """WebSocket message builder"""

    def __init__(self) -> None:
        self._sequence = 0

    def _get_next_sequence(self) -> int:
        """Get next sequence number"""
        self._sequence += 1
        return self._sequence

    def _create_header(self, message_type: MessageType) -> dict[str, Any]:
        """Create message header"""
        return {
            "version": "1.0",
            "message_type": message_type.value,
            "timestamp": datetime.now().isoformat(),
            "sequence": self._get_next_sequence(),
        }

    def create_connect_request(self) -> dict[str, Any]:
        """Create connection request"""
        return {
            "header": self._create_header(MessageType.CONNECT_REQUEST),
            "payload": {}
        }

    def create_session_request(self) -> dict[str, Any]:
        """Create session request"""
        return {
            "header": self._create_header(MessageType.SESSION_REQUEST),
            "payload": {}
        }

    def create_synthesis_start(self, session_id: str) -> dict[str, Any]:
        """Create synthesis start message"""
        return {
            "header": self._create_header(MessageType.SYNTHESIS_START),
            "payload": {"session_id": session_id}
        }

    def create_text_request(
        self,
        session_id: str,
        text: str,
        mode: str = "zero_shot",
        prompt_text: str = "",
        speed: float = 1.0,
        output_format: str = "wav",
        sample_rate: int | None = None,
        zero_shot_spk_id: str | None = None,
        spk_id: str | None = None,
        instruct_text: str | None = None,
        bit_rate: int | None = None,
        compression_level: int | None = None,
    ) -> dict[str, Any]:
        """Create text request message"""
        params = {
            "text": text,
            "mode": mode,
            "prompt_text": prompt_text,
            "speed": speed,
            "output_format": output_format,
        }

        # Add optional parameters
        if sample_rate is not None:
            params["sample_rate"] = sample_rate
        if zero_shot_spk_id is not None:
            params["zero_shot_spk_id"] = zero_shot_spk_id
        if spk_id is not None:
            params["spk_id"] = spk_id
        if instruct_text is not None:
            params["instruct_text"] = instruct_text
        if bit_rate is not None:
            params["bit_rate"] = bit_rate
        if compression_level is not None:
            params["compression_level"] = compression_level

        return {
            "header": self._create_header(MessageType.TEXT_REQUEST),
            "payload": {
                "session_id": session_id,
                "params": params
            }
        }

    def create_synthesis_end(self, session_id: str) -> dict[str, Any]:
        """Create synthesis end message"""
        return {
            "header": self._create_header(MessageType.SYNTHESIS_END),
            "payload": {"session_id": session_id}
        }

    def create_session_end(self, session_id: str) -> dict[str, Any]:
        """Create session end message"""
        return {
            "header": self._create_header(MessageType.SESSION_END),
            "payload": {"session_id": session_id}
        }


class WebSocketProtocol:
    """WebSocket protocol handler"""

    def __init__(self) -> None:
        self.message_builder = MessageBuilder()

    def serialize_message(self, message: dict[str, Any]) -> str:
        """Serialize message to JSON string"""
        try:
            return json.dumps(message, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Message serialization failed: {e!s}") from e

    def deserialize_message(self, data: str) -> dict[str, Any]:
        """Deserialize JSON string to message"""
        try:
            message = json.loads(data)
            self._validate_message_format(message)
            # Type assertion since _validate_message_format ensures it's a dict
            return message  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise ValidationError(f"Message deserialization failed: {e!s}") from e

    def _validate_message_format(self, message: dict[str, Any]) -> None:
        """Validate message format"""
        if not isinstance(message, dict):
            raise ValidationError("Message must be dictionary format") from None

        if "header" not in message:
            raise ValidationError("Message missing header field") from None

        if "payload" not in message:
            raise ValidationError("Message missing payload field") from None

        header = message["header"]
        if not isinstance(header, dict):
            raise ValidationError("Header must be dictionary format") from None

        required_header_fields = ["version", "message_type", "timestamp", "sequence"]
        for field in required_header_fields:
            if field not in header:
                raise ValidationError(f"Header missing {field} field") from None

    def get_message_type(self, message: dict[str, Any]) -> MessageType:
        """Get message type"""
        try:
            message_type_str = message["header"]["message_type"]
            return MessageType(message_type_str)
        except (KeyError, ValueError) as e:
            raise ValidationError(f"Invalid message type: {e!s}") from e

    def get_session_id(self, message: dict[str, Any]) -> str | None:
        """Get session ID"""
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            return None
        session_id = payload.get("session_id")
        return session_id if isinstance(session_id, str) else None

    def extract_audio_data(self, message: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
        """Extract audio data and metadata"""
        payload = message.get("payload", {})

        # Get base64 encoded audio data
        import base64
        audio_base64 = payload.get("audio_data")
        if not audio_base64:
            raise ValidationError("No audio data in message") from None

        try:
            audio_data = base64.b64decode(audio_base64)
        except Exception as e:
            raise ValidationError(f"Audio data decoding failed: {e!s}") from e

        # Extract metadata
        metadata = {
            "session_id": payload.get("session_id"),
            "text_index": payload.get("text_index"),
            "chunk_index": payload.get("chunk_index"),
        }

        return audio_data, metadata

    def extract_error_info(self, message: dict[str, Any]) -> dict[str, Any]:
        """Extract error information"""
        payload = message.get("payload", {})

        if payload.get("status") == "error" and "error" in payload:
            error_info = payload["error"]
            return {
                "code": error_info.get("code", "UNKNOWN_ERROR"),
                "message": error_info.get("message", "Unknown error"),
                "details": error_info.get("details", {}),
                "request_id": error_info.get("request_id", ""),
            }

        return {}

    def is_error_message(self, message: dict[str, Any]) -> bool:
        """Check if it's an error message"""
        payload = message.get("payload", {})
        return payload.get("status") == "error" and "error" in payload
