"""Streaming synthesis session management

Manages the lifecycle of a single speech synthesis session.
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from ..models.synthesis import SynthesisConfig, SynthesisResult
from ..utils.exceptions import CosyVoiceError, InvalidStateError
from .client import StreamWebSocketClient

logger = logging.getLogger(__name__)


class StreamSession:
    """Streaming synthesis session

    Manages the lifecycle of a single session, including creation, synthesis, and termination.
    """

    def __init__(
        self,
        client: StreamWebSocketClient,
        session_id: str | None = None
    ) -> None:
        self.client = client
        self.session_id = session_id
        self._is_active = False
        self._is_synthesizing = False

        # Audio data collection
        self._audio_queue: asyncio.Queue[SynthesisResult | None] = asyncio.Queue()
        self._synthesis_complete_event = asyncio.Event()
        self._error: Exception | None = None

        # Session timing
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None

        # Set up callbacks
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """Set up client callbacks"""
        self.client.set_audio_chunk_callback(self._on_audio_chunk)
        self.client.set_synthesis_complete_callback(self._on_synthesis_complete)
        self.client.set_error_callback(self._on_error)

    @property
    def is_active(self) -> bool:
        """Whether the session is active"""
        return self._is_active

    @property
    def is_synthesizing(self) -> bool:
        """Whether synthesis is in progress"""
        return self._is_synthesizing

    async def start(self) -> str:
        """Start the session"""
        if self._is_active:
            raise InvalidStateError("Session already started")

        if not self.client.is_connected:
            raise InvalidStateError("Client not connected")

        # Create session
        if not self.session_id:
            self.session_id = await self.client.create_session()

        self._is_active = True
        logger.info(f"Session started: {self.session_id}")
        return self.session_id

    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        config: SynthesisConfig
    ) -> AsyncIterator[SynthesisResult]:
        """Streaming speech synthesis

        Args:
            text_stream: Asynchronous text stream
            config: Synthesis configuration

        Yields:
            SynthesisResult: Audio synthesis result
        """
        if not self._is_active:
            raise InvalidStateError("Session not started")

        if self.session_id is None:
            raise InvalidStateError("Session ID not available")

        if self._is_synthesizing:
            raise InvalidStateError("Another synthesis task is in progress")

        try:
            self._is_synthesizing = True
            self._start_time = datetime.now()
            self._synthesis_complete_event.clear()

            # Start synthesis
            await self.client.start_synthesis(self.session_id)

            # Start text sending task
            text_task = asyncio.create_task(
                self._send_text_stream(text_stream, config)
            )

            # Generate audio results asynchronously
            try:
                while True:
                    # Wait for audio data
                    result = await self._audio_queue.get()

                    # Check for errors
                    if self._error:
                        raise self._error

                    # None indicates synthesis completion
                    if result is None:
                        break

                    # Only return audio for current session
                    if result.session_id == self.session_id:
                        yield result

            finally:
                # Ensure text sending task completes
                if not text_task.done():
                    text_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await text_task

                # Wait for synthesis completion
                try:
                    await asyncio.wait_for(
                        self._synthesis_complete_event.wait(),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Synthesis completion timeout")

                self._is_synthesizing = False
                self._end_time = datetime.now()

        except Exception as e:
            self._is_synthesizing = False
            self._error = e
            raise

    async def synthesize_text(
        self,
        text: str,
        config: SynthesisConfig
    ) -> AsyncIterator[SynthesisResult]:
        """Single text synthesis

        Args:
            text: Text to synthesize
            config: Synthesis configuration

        Yields:
            SynthesisResult: Audio synthesis result
        """
        async def single_text_stream() -> AsyncIterator[str]:
            yield text

        async for result in self.synthesize_stream(single_text_stream(), config):
            yield result

    async def end(self) -> None:
        """End the session"""
        if not self._is_active:
            return

        if self.session_id is None:
            logger.warning("Cannot end session: session_id is None")
            return

        try:
            if self._is_synthesizing:
                await self.client.end_synthesis(self.session_id)
                self._is_synthesizing = False

            # Send end session request
            await self.client.end_session(self.session_id)

            # Wait for server to confirm session ended, but with timeout
            # to avoid hanging if server doesn't respond
            session_ended = await self.client.wait_for_session_ended(timeout=5.0)
            if not session_ended:
                logger.warning(f"Timeout waiting for session end confirmation: {self.session_id}")
                # Force cleanup on timeout
                await self._force_cleanup()

        except Exception as e:
            logger.error(f"Error ending session: {e!s}")
            # Force cleanup on error
            await self._force_cleanup()
        finally:
            self._is_active = False
            logger.info(f"Session ended: {self.session_id}")

    async def _send_text_stream(
        self,
        text_stream: AsyncIterator[str],
        config: SynthesisConfig
    ) -> None:
        """Send text stream"""
        if self.session_id is None:
            raise InvalidStateError("Session ID not available")

        try:
            async for text in text_stream:
                if not text.strip():
                    continue

                await self.client.send_text(
                    session_id=self.session_id,
                    text=text,
                    mode=config.mode,
                    prompt_text="",  # Retrieved from cache on server side
                    speed=config.speed,
                    output_format=config.output_format,
                    sample_rate=config.sample_rate,
                    zero_shot_spk_id=config.speaker_id if config.mode != "sft" else None,
                    spk_id=config.speaker_id if config.mode == "sft" else None,
                    instruct_text=config.instruct_text,
                    bit_rate=config.bit_rate,
                    compression_level=config.compression_level,
                )

                logger.debug(f"Sent text: {text[:50]}...")

            # Send synthesis end signal
            await self.client.end_synthesis(self.session_id)

        except Exception as e:
            logger.error(f"Error sending text stream: {e!s}")
            self._error = e

    async def _force_cleanup(self) -> None:
        """Force cleanup session state on client side"""
        # Directly clear the session state on client if server doesn't respond
        if hasattr(self.client, '_current_session_id') and self.client._current_session_id == self.session_id:
            self.client._current_session_id = None
            self.client._synth_active = False
            logger.warning(f"Forced cleanup of session state: {self.session_id}")

    # Callback methods
    async def _on_audio_chunk(self, result: SynthesisResult) -> None:
        """Audio chunk callback"""
        if result.session_id == self.session_id:
            await self._audio_queue.put(result)

    async def _on_synthesis_complete(self, session_id: str) -> None:
        """Synthesis completion callback"""
        if session_id == self.session_id:
            await self._audio_queue.put(None)  # End signal
            self._synthesis_complete_event.set()

    async def _on_error(self, error: CosyVoiceError) -> None:
        """Error callback"""
        self._error = error
        await self._audio_queue.put(None)  # End signal
        self._synthesis_complete_event.set()

    # Context manager support
    async def __aenter__(self) -> 'StreamSession':
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.end()


@asynccontextmanager
async def create_stream_session(
    client: StreamWebSocketClient,
    session_id: str | None = None
) -> AsyncIterator[StreamSession]:
    """Create streaming synthesis session context manager

    Args:
        client: WebSocket client
        session_id: Optional session ID

    Yields:
        StreamSession: Streaming synthesis session
    """
    session = StreamSession(client, session_id)
    try:
        await session.start()
        yield session
    finally:
        await session.end()
