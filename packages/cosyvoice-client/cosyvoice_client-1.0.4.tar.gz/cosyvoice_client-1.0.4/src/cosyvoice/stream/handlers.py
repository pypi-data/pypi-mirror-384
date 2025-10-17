"""Message handlers

Handle various WebSocket messages received from the server.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from ..models.enums import MessageType
from ..models.synthesis import SynthesisResult
from ..utils.exceptions import CosyVoiceError
from .protocol import WebSocketProtocol

logger = logging.getLogger(__name__)


class MessageHandler:
    """WebSocket message handler"""

    def __init__(self, protocol: WebSocketProtocol) -> None:
        self.protocol = protocol

        # Event callbacks
        self._on_connected: Callable[[], Awaitable[None]] | None = None
        self._on_session_created: Callable[[str], Awaitable[None]] | None = None
        self._on_synthesis_started: Callable[[str], Awaitable[None]] | None = None
        self._on_audio_chunk: Callable[[SynthesisResult], Awaitable[None]] | None = None
        self._on_audio_complete: Callable[[str, int], Awaitable[None]] | None = None
        self._on_synthesis_complete: Callable[[str], Awaitable[None]] | None = None
        self._on_session_ended: Callable[[str], Awaitable[None]] | None = None
        self._on_error: Callable[[CosyVoiceError], Awaitable[None]] | None = None

        # Simple metrics tracking for RTF/FFTB calculation
        self._session_metrics: dict[str, dict[str, Any]] = {}

    # Set callback functions
    def set_connected_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Set connection success callback"""
        self._on_connected = callback

    def set_session_created_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set session creation callback"""
        self._on_session_created = callback

    def set_synthesis_started_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set synthesis start callback"""
        self._on_synthesis_started = callback

    def set_audio_chunk_callback(self, callback: Callable[[SynthesisResult], Awaitable[None]]) -> None:
        """Set audio chunk callback"""
        self._on_audio_chunk = callback

    def set_audio_complete_callback(self, callback: Callable[[str, int], Awaitable[None]]) -> None:
        """Set audio complete callback"""
        self._on_audio_complete = callback

    def set_synthesis_complete_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set synthesis complete callback"""
        self._on_synthesis_complete = callback

    def set_session_ended_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set session end callback"""
        self._on_session_ended = callback

    def set_error_callback(self, callback: Callable[[CosyVoiceError], Awaitable[None]]) -> None:
        """Set error callback"""
        self._on_error = callback

    async def handle_message(self, message_data: str) -> None:
        """Handle received message"""
        try:
            message = self.protocol.deserialize_message(message_data)

            # Check if it's an error message
            if self.protocol.is_error_message(message):
                await self._handle_error_message(message)
                return

            # Dispatch handling based on message type
            message_type = self.protocol.get_message_type(message)

            handler_map = {
                MessageType.CONNECT_RESPONSE: self._handle_connect_response,
                MessageType.SESSION_RESPONSE: self._handle_session_response,
                MessageType.SYNTHESIS_START_ACK: self._handle_synthesis_start_ack,
                MessageType.TEXT_ACCEPTED: self._handle_text_accepted,
                MessageType.AUDIO_RESPONSE: self._handle_audio_response,
                MessageType.AUDIO_COMPLETE: self._handle_audio_complete,
                MessageType.SYNTHESIS_END_ACK: self._handle_synthesis_end_ack,
                MessageType.SESSION_END_ACK: self._handle_session_end_ack,
            }

            handler = handler_map.get(message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Message handling failed: {e!s}", exc_info=True)
            if self._on_error:
                error = CosyVoiceError(f"Message handling failed: {e!s}")
                await self._on_error(error)

    async def _handle_connect_response(self, message: dict[str, Any]) -> None:
        """Handle connection response"""
        logger.info("WebSocket connection successful")
        if self._on_connected:
            await self._on_connected()

    async def _handle_session_response(self, message: dict[str, Any]) -> None:
        """Handle session response"""
        session_id = message["payload"].get("session_id")
        if session_id:
            logger.info(f"Session created successfully: {session_id}")
            # Initialize simple metrics tracking for RTF/FFTB
            self._session_metrics[session_id] = {
                "start_time": datetime.now(),
                "text_length": 0,
                "audio_duration": 0.0,
                "first_chunk_time": None,
            }
            if self._on_session_created:
                await self._on_session_created(session_id)

    async def _handle_synthesis_start_ack(self, message: dict[str, Any]) -> None:
        """Handle synthesis start acknowledgment"""
        session_id = self.protocol.get_session_id(message)
        if session_id:
            logger.info(f"Synthesis started: {session_id}")

            # Track text length for RTF calculation
            text_info = message.get("payload", {}).get("text_info", {})
            text_length = len(text_info.get("text", ""))
            if session_id in self._session_metrics:
                self._session_metrics[session_id]["text_length"] = text_length

            if self._on_synthesis_started:
                await self._on_synthesis_started(session_id)

    async def _handle_text_accepted(self, message: dict[str, Any]) -> None:
        """Handle text acceptance confirmation"""
        payload = message.get("payload", {})
        status = payload.get("status")
        if status != "queued":
            logger.warning(f"Text processing status abnormal: {status}")

    async def _handle_audio_response(self, message: dict[str, Any]) -> None:
        """Handle audio response"""
        try:
            audio_data, metadata = self.protocol.extract_audio_data(message)
            session_id = metadata.get("session_id")

            # Update metrics for RTF/FFTB calculation
            if session_id and session_id in self._session_metrics:
                metrics = self._session_metrics[session_id]

                # Record first chunk time for FFTB
                if metrics["first_chunk_time"] is None:
                    metrics["first_chunk_time"] = datetime.now()

                # Update audio duration for RTF calculation
                audio_duration = metadata.get("duration", 0.0)
                if audio_duration > 0:
                    metrics["audio_duration"] += audio_duration

            # Create synthesis result
            result = SynthesisResult(
                audio_data=audio_data,
                session_id=metadata.get("session_id", ""),
                text_index=metadata.get("text_index", 0),
                chunk_index=metadata.get("chunk_index", 0),
                metadata=metadata,
                timestamp=datetime.now(),
            )

            if self._on_audio_chunk:
                await self._on_audio_chunk(result)

        except Exception as e:
            logger.error(f"Failed to process audio response: {e!s}")
            if self._on_error:
                error = CosyVoiceError(f"Audio processing failed: {e!s}")
                await self._on_error(error)

    async def _handle_audio_complete(self, message: dict[str, Any]) -> None:
        """Handle audio completion notification"""
        payload = message.get("payload", {})
        session_id = payload.get("session_id")
        text_index = payload.get("text_index", 0)

        if session_id:
            logger.debug(f"Audio complete: session={session_id}, text_index={text_index}")
            if self._on_audio_complete:
                await self._on_audio_complete(session_id, text_index)

    async def _handle_synthesis_end_ack(self, message: dict[str, Any]) -> None:
        """Handle synthesis end acknowledgment"""
        session_id = self.protocol.get_session_id(message)
        if session_id:
            logger.info(f"Synthesis ended: {session_id}")

            # Simple completion callback without complex statistics
            if self._on_synthesis_complete:
                await self._on_synthesis_complete(session_id)

    async def _handle_session_end_ack(self, message: dict[str, Any]) -> None:
        """Handle session end acknowledgment"""
        session_id = self.protocol.get_session_id(message)
        if session_id:
            logger.info(f"Session end acknowledged: {session_id}")

            # Calculate and log final metrics before cleanup
            if session_id in self._session_metrics:
                metrics = self._session_metrics[session_id]
                end_time = datetime.now()
                total_time = (end_time - metrics["start_time"]).total_seconds()

                # Calculate and log RTF (Real-Time Factor)
                if metrics["audio_duration"] > 0 and total_time > 0:
                    rtf = total_time / metrics["audio_duration"]
                    logger.info(f"Session {session_id} - RTF: {rtf:.3f}")

                # Calculate and log FFTB (First Frame Time to Begin)
                if metrics["first_chunk_time"]:
                    fftb = (metrics["first_chunk_time"] - metrics["start_time"]).total_seconds()
                    logger.info(f"Session {session_id} - FFTB: {fftb:.3f}s")

                # Clean up metrics
                del self._session_metrics[session_id]

            if self._on_session_ended:
                await self._on_session_ended(session_id)

    async def _handle_error_message(self, message: dict[str, Any]) -> None:
        """Handle error messages"""
        error_info = self.protocol.extract_error_info(message)

        error_code = error_info.get("code", "UNKNOWN_ERROR")
        error_message = error_info.get("message", "Unknown error")
        error_details = error_info.get("details", {})

        logger.error(f"Server error: [{error_code}] {error_message}")

        if self._on_error:
            error = CosyVoiceError(
                message=f"[{error_code}] {error_message}",
                error_code=error_code,
                details=error_details
            )
            await self._on_error(error)
