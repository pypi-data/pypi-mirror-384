"""WebSocket streaming client

Asynchronous WebSocket client implementation based on websockets library.
"""

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..models.enums import ClientState
from ..models.synthesis import SynthesisResult
from ..utils.exceptions import (
    ConnectionError,
    CosyVoiceError,
    InvalidStateError,
    TimeoutError,
    WebSocketError,
)
from .handlers import MessageHandler
from .protocol import WebSocketProtocol

logger = logging.getLogger(__name__)


class StreamWebSocketClient:
    """Asynchronous WebSocket streaming client"""

    def __init__(
        self,
        server_url: str,
        api_key: str | None = None,
        connect_timeout: float = 30.0,
        ping_interval: float = 20.0,
        ping_timeout: float = 10.0,
        close_timeout: float = 10.0,
        max_reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.server_url = self._normalize_url(server_url)
        self.connect_timeout = connect_timeout
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.close_timeout = close_timeout
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay

        # WebSocket connection + decomposed state flags
        self._websocket: Any = None
        # Transport/connection state only
        self._connection_state: ClientState = ClientState.DISCONNECTED
        # Active session id (None => no session)
        self._current_session_id: str | None = None
        # Whether synthesis is currently active within the session
        self._synth_active: bool = False

        # Protocol and message handling
        self.protocol = WebSocketProtocol()
        self.message_handler = MessageHandler(self.protocol)

        # Event loop tasks
        self._receive_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._connection_lost_task: asyncio.Task | None = None

        # Synchronization primitives
        self._connect_event = asyncio.Event()
        self._session_event = asyncio.Event()
        self._synthesis_event = asyncio.Event()
        self._session_ended_event = asyncio.Event()  # Event for session end confirmation

        # Reconnection state
        self._reconnect_attempts = 0
        self._should_reconnect = True

        # Set up internal callbacks
        self._setup_internal_callbacks()

    def _normalize_url(self, url: str) -> str:
        """Normalize WebSocket URL"""
        parsed = urlparse(url)

        if parsed.scheme not in ('ws', 'wss', 'http', 'https'):
            raise ValueError(f"Unsupported protocol: {parsed.scheme}")

        # Convert HTTP protocol to WebSocket
        if parsed.scheme == 'http':
            scheme = 'ws'
        elif parsed.scheme == 'https':
            scheme = 'wss'
        else:
            scheme = parsed.scheme

        # Ensure path ends with /ws/tts
        path = parsed.path.rstrip('/')
        if not path.endswith('/ws/tts'):
            if path:
                path += '/ws/tts'
            else:
                path = '/ws/tts'

        # Add API key as query parameter
        query = parsed.query
        if self.api_key:
            if query:
                query += f"&token={self.api_key}"
            else:
                query = f"token={self.api_key}"

        return f"{scheme}://{parsed.netloc}{path}" + (f"?{query}" if query else "")

    def _setup_internal_callbacks(self) -> None:
        """Set up internal event callbacks"""
        self.message_handler.set_connected_callback(self._on_connected)
        self.message_handler.set_session_created_callback(self._on_session_created)
        self.message_handler.set_synthesis_started_callback(self._on_synthesis_started)
        self.message_handler.set_session_ended_callback(self._on_session_ended)
        self.message_handler.set_error_callback(self._on_internal_error)

    @property
    def state(self) -> ClientState:
        """Derived high-level state (backward compatible with previous single _state).

        Resolution priority:
          1. Connection lifecycle terminal / transitional states (DISCONNECTED, CONNECTING, CLOSING, ERROR)
          2. If connected but no session: CONNECTED
          3. If session and not synthesizing: SESSION_ACTIVE
          4. If session and synthesizing: SYNTHESIZING
        """
        if self._connection_state in (
            ClientState.DISCONNECTED,
            ClientState.CONNECTING,
            ClientState.CLOSING,
            ClientState.ERROR,
        ):
            return self._connection_state
        if self._current_session_id is None:
            return ClientState.CONNECTED
        if self._synth_active:
            return ClientState.SYNTHESIZING
        return ClientState.SESSION_ACTIVE

    @property
    def is_connected(self) -> bool:
        """Whether WebSocket transport established (independent of session)."""
        return self._connection_state == ClientState.CONNECTED

    @property
    def current_session_id(self) -> str | None:
        """Current session ID"""
        return self._current_session_id

    # Public methods
    async def connect_websocket(self) -> None:
        """Connect to server"""
        if self._connection_state != ClientState.DISCONNECTED:
            raise InvalidStateError(f"Cannot connect from state {self._connection_state}")

        self._connection_state = ClientState.CONNECTING
        self._should_reconnect = True
        self._reconnect_attempts = 0

        try:
            await self._connect_with_retry()
        except Exception as e:
            self._connection_state = ClientState.ERROR
            raise ConnectionError(f"Connection failed: {e!s}") from e

    async def create_session(self) -> str:
        """Create new session"""
        if self._connection_state != ClientState.CONNECTED:
            raise InvalidStateError(f"Must be connected to create session, current connection state: {self._connection_state}")
        if self._current_session_id is not None:
            raise InvalidStateError("A session is already active; end it before creating a new one")

        self._session_event.clear()

        # Send session creation request
        request = self.protocol.message_builder.create_session_request()
        await self._send_message(request)

        # Wait for session creation response
        try:
            await asyncio.wait_for(self._session_event.wait(), timeout=10.0)
            if self._current_session_id:
                return self._current_session_id  # type: ignore[unreachable]

            raise CosyVoiceError("Session creation failed: No valid session ID received")
        except asyncio.TimeoutError:
            raise TimeoutError("Session creation timeout") from None

    async def start_synthesis(self, session_id: str) -> None:
        """Start speech synthesis"""
        if self._current_session_id is None:
            raise InvalidStateError("No active session. Call create_session() first")
        if self._synth_active:
            raise InvalidStateError("Synthesis already active")

        if session_id != self._current_session_id:
            raise ValueError(f"Session ID mismatch: {session_id} != {self._current_session_id}")

        self._synthesis_event.clear()

        # Send synthesis start request
        request = self.protocol.message_builder.create_synthesis_start(session_id)
        await self._send_message(request)

        # Wait for synthesis start response
        try:
            await asyncio.wait_for(self._synthesis_event.wait(), timeout=10.0)
            self._synth_active = True
        except asyncio.TimeoutError:
            raise TimeoutError("Synthesis start timeout") from None

    async def send_text(
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
    ) -> None:
        """Send text synthesis request"""
        if not self._synth_active:
            raise InvalidStateError("Synthesis not active; call start_synthesis first")

        if session_id != self._current_session_id:
            raise ValueError(f"Session ID mismatch: {session_id} != {self._current_session_id}")

        # Create text request
        request = self.protocol.message_builder.create_text_request(
            session_id=session_id,
            text=text,
            mode=mode,
            prompt_text=prompt_text,
            speed=speed,
            output_format=output_format,
            sample_rate=sample_rate,
            zero_shot_spk_id=zero_shot_spk_id,
            spk_id=spk_id,
            instruct_text=instruct_text,
            bit_rate=bit_rate,
            compression_level=compression_level,
        )

        await self._send_message(request)

    async def end_synthesis(self, session_id: str) -> None:
        """End speech synthesis"""
        if not self._synth_active:
            raise InvalidStateError("Synthesis not active")

        if session_id != self._current_session_id:
            raise ValueError(f"Session ID mismatch: {session_id} != {self._current_session_id}")

        # Send synthesis end request
        request = self.protocol.message_builder.create_synthesis_end(session_id)
        await self._send_message(request)

        self._synth_active = False
        # After ending synthesis session remains active.

    async def end_session(self, session_id: str) -> None:
        """End session"""
        if self._current_session_id is None:
            raise InvalidStateError("No active session to end")
        if self._synth_active:
            raise InvalidStateError("Cannot end session while synthesis active; end synthesis first")

        if session_id != self._current_session_id:
            raise ValueError(f"Session ID mismatch: {session_id} != {self._current_session_id}")

        # Clear the event before sending request
        self._session_ended_event.clear()

        # Send session end request
        request = self.protocol.message_builder.create_session_end(session_id)
        await self._send_message(request)

    async def wait_for_session_ended(self, timeout: float = 10.0) -> bool:
        """Wait for session end confirmation from server

        Args:
            timeout: Timeout in seconds

        Returns:
            True if session ended, False if timeout
        """
        try:
            await asyncio.wait_for(self._session_ended_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def close(self) -> None:
        """Close connection"""
        self._should_reconnect = False
        self._connection_state = ClientState.CLOSING

        try:
            # Cancel background tasks
            if self._receive_task and not self._receive_task.done():
                self._receive_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._receive_task

            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._heartbeat_task

            # Close WebSocket connection
            if self._websocket:
                try:
                    if hasattr(self._websocket, 'close'):
                        await self._websocket.close()
                except Exception:
                    # Ignore any close errors
                    pass

        except Exception as e:
            logger.error(f"Error closing connection: {e!s}")
        finally:
            self._connection_state = ClientState.DISCONNECTED
            self._current_session_id = None
            self._synth_active = False
            self._websocket = None

    # Event callback setup methods
    def set_audio_chunk_callback(self, callback: Callable[[SynthesisResult], Awaitable[None]]) -> None:
        """Set audio chunk callback"""
        self.message_handler.set_audio_chunk_callback(callback)

    def set_audio_complete_callback(self, callback: Callable[[str, int], Awaitable[None]]) -> None:
        """Set audio complete callback"""
        self.message_handler.set_audio_complete_callback(callback)

    def set_synthesis_complete_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Set synthesis complete callback"""
        self.message_handler.set_synthesis_complete_callback(callback)

    def set_error_callback(self, callback: Callable[[CosyVoiceError], Awaitable[None]]) -> None:
        """Set error callback"""
        self.message_handler.set_error_callback(callback)

    # Internal methods
    async def _connect_with_retry(self) -> None:
        """Connect with retry logic"""
        while self._reconnect_attempts < self.max_reconnect_attempts and self._should_reconnect:
            try:
                await self._establish_connection()
                return
            except Exception as e:
                self._reconnect_attempts += 1
                logger.warning(f"Connection failed (attempt {self._reconnect_attempts}/{self.max_reconnect_attempts}): {e!s}")

                if self._reconnect_attempts < self.max_reconnect_attempts and self._should_reconnect:
                    await asyncio.sleep(self.reconnect_delay * self._reconnect_attempts)
                else:
                    raise

    async def _establish_connection(self) -> None:
        """Establish WebSocket connection"""
        logger.info(f"Connecting to: {self.server_url}")

        try:
            self._websocket = await asyncio.wait_for(
                connect(
                    self.server_url,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout,
                    close_timeout=self.close_timeout,
                ),
                timeout=self.connect_timeout
            )

            logger.info("WebSocket connection established successfully")

            # Start message receiving task
            self._receive_task = asyncio.create_task(self._message_receive_loop())

            # Send connection request
            self._connect_event.clear()
            request = self.protocol.message_builder.create_connect_request()
            await self._send_message(request)

            # Wait for connection confirmation
            await asyncio.wait_for(self._connect_event.wait(), timeout=10.0)

        except asyncio.TimeoutError:
            raise TimeoutError("Connection timeout") from None
        except WebSocketException as e:
            raise WebSocketError(f"WebSocket connection failed: {e!s}") from e

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send message"""
        if not self._websocket:
            raise ConnectionError("WebSocket connection not established")

        # Check if WebSocket is closed
        if hasattr(self._websocket, 'closed') and self._websocket.closed:
            raise ConnectionError("WebSocket connection closed")

        try:
            message_str = self.protocol.serialize_message(message)
            await self._websocket.send(message_str)
            logger.debug(f"Sent message: {message['header']['message_type']}")
        except ConnectionClosed:
            raise ConnectionError("WebSocket connection closed") from None
        except Exception as e:
            raise ConnectionError(f"Failed to send message: {e!s}") from e

    async def _message_receive_loop(self) -> None:
        """Message receiving loop"""
        try:
            while self._websocket and self._should_reconnect:
                # Check if WebSocket is closed
                if hasattr(self._websocket, 'closed') and self._websocket.closed:
                    logger.warning("WebSocket connection closed")
                    break

                try:
                    message = await self._websocket.recv()
                    await self.message_handler.handle_message(message)
                except ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e!s}")

        except Exception as e:
            logger.error(f"Error in message receiving loop: {e!s}")
        finally:
            # Connection lost, attempt reconnection
            if self._should_reconnect and self._connection_state != ClientState.CLOSING:
                self._connection_lost_task = asyncio.create_task(self._handle_disconnection())

    async def _handle_disconnection(self) -> None:
        """Handle connection disconnection"""
        logger.warning("Connection lost, attempting reconnection...")
        self._connection_state = ClientState.DISCONNECTED
        self._current_session_id = None
        self._synth_active = False

        if self._should_reconnect:
            try:
                await self._connect_with_retry()
            except Exception as e:
                logger.error(f"Reconnection failed: {e!s}")
                self._connection_state = ClientState.ERROR

    # Internal event callbacks
    async def _on_connected(self) -> None:
        """Connection success callback"""
        self._connection_state = ClientState.CONNECTED
        self._reconnect_attempts = 0
        self._connect_event.set()
        logger.info("WebSocket connection confirmed")

    async def _on_session_created(self, session_id: str) -> None:
        """Session creation callback"""
        self._current_session_id = session_id
        self._session_event.set()
        logger.info(f"Session created successfully: {session_id}")

    async def _on_synthesis_started(self, session_id: str) -> None:
        """Synthesis start callback"""
        self._synthesis_event.set()
        logger.info(f"Synthesis started: {session_id}")

    async def _on_session_ended(self, session_id: str) -> None:
        """Session end callback"""
        if session_id == self._current_session_id:
            self._current_session_id = None
            self._synth_active = False
            # Signal that session has ended
            self._session_ended_event.set()
            # Transport still connected
            logger.info(f"Session ended: {session_id}")

    async def _on_internal_error(self, error: CosyVoiceError) -> None:
        """Internal error callback"""
        logger.error(f"Internal error: {error}")
        self._connection_state = ClientState.ERROR
        self._synth_active = False
