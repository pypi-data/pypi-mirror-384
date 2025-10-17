"""CosyVoice Async Streaming Client

Provides unified TTS client interface, integrating WebSocket streaming synthesis and speaker management functionality.
"""
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from ._internal.config import ClientConfig, load_config_from_env
from .models.enums import ClientState
from .models.synthesis import SynthesisConfig, SynthesisResult
from .speaker.manager import SpeakerManager
from .stream.client import StreamWebSocketClient
from .stream.session import StreamSession
from .utils.audio import merge_audio_chunks
from .utils.exceptions import (
    CosyVoiceError,
    InvalidStateError,
)
from .utils.validation import validate_text_content, validate_url

logger = logging.getLogger(__name__)


# Type aliases
AudioStreamHandler = Callable[[SynthesisResult], Awaitable[None]]
SynthesisCompleteHandler = Callable[[str], Awaitable[None]]  # Only session_id needed
ErrorHandler = Callable[[CosyVoiceError], Awaitable[None]]


class StreamClient:
    """CosyVoice async streaming TTS client

    This is the main entry point of the SDK, providing complete TTS and speaker management functionality.

    Features:
    - Async WebSocket streaming synthesis
    - Complete speaker management functionality
    - Event-driven audio processing
    - Automatic connection management and reconnection
    - Type-safe API

    Example:
        >>> async with cosyvoice.create_client("wss://api.cosyvoice.com") as client:
        ...     # Create speaker
        ...     speaker_id = await client.speaker.create("Reference text", "my_speaker", "voice.wav")
        ...
        ...     # Configure synthesis parameters
        ...     config = cosyvoice.SynthesisConfig(speaker_id=speaker_id)
        ...
        ...     # Streaming synthesis
        ...     async for chunk in client.synthesize_text("Hello World", config):
        ...         # Process audio chunk
        ...         process_audio(chunk)
    """

    def __init__(
        self,
        server_url: str | None = None,
        api_key: str | None = None,
        config: ClientConfig | None = None,
        connect_timeout: float | None = None,
        request_timeout: float | None = None,
        ping_interval: float | None = None,
        max_reconnect_attempts: int | None = None,
        reconnect_delay: float | None = None,
    ) -> None:
        """Initialize client

        Args:
            server_url: Server URL (supports ws/wss/http/https), takes precedence over config and environment variables
            api_key: API key, takes precedence over config and environment variables
            config: Client configuration object, will load from environment variables if not provided
            connect_timeout: Connection timeout in seconds
            request_timeout: Request timeout in seconds
            ping_interval: WebSocket ping interval in seconds
            max_reconnect_attempts: Maximum number of reconnection attempts
            reconnect_delay: Reconnection delay in seconds
        """
        # Load configuration
        if config is None:
            config = load_config_from_env()

        # Override configuration with parameters
        if server_url is not None:
            config.base_url = server_url
        if api_key is not None:
            config.api_key = api_key
        if connect_timeout is not None:
            config.connection_timeout = connect_timeout
        if request_timeout is not None:
            config.read_timeout = request_timeout
        if ping_interval is not None:
            config.ping_interval = ping_interval
        if max_reconnect_attempts is not None:
            config.max_reconnect_attempts = max_reconnect_attempts
        if reconnect_delay is not None:
            config.base_reconnect_delay = reconnect_delay

        # Validate final configuration
        config.validate()
        validate_url(config.base_url)

        self.config = config

        # Create WebSocket client
        self._ws_client = StreamWebSocketClient(
            server_url=config.base_url,
            api_key=config.api_key,
            connect_timeout=config.connection_timeout,
            ping_interval=config.ping_interval,
            ping_timeout=config.ping_timeout,
            close_timeout=config.close_timeout,
            max_reconnect_attempts=config.max_reconnect_attempts,
            reconnect_delay=config.base_reconnect_delay,
        )

        # Create speaker manager
        self.speaker = SpeakerManager(
            server_url=config.base_url,
            api_key=config.api_key,
            timeout=config.read_timeout,
            max_retries=config.max_reconnect_attempts,
            retry_delay=config.base_reconnect_delay,
        )

        # Current session
        self._current_session: StreamSession | None = None
        self._session_config: SynthesisConfig | None = None

        # Global event callbacks
        self._audio_chunk_handler: AudioStreamHandler | None = None
        self._synthesis_complete_handler: SynthesisCompleteHandler | None = None
        self._error_handler: ErrorHandler | None = None

    @property
    def state(self) -> ClientState:
        """Current client state"""
        return self._ws_client.state

    @property
    def is_connected(self) -> bool:
        """Whether connected to server"""
        return self._ws_client.is_connected

    @property
    def current_session_id(self) -> str | None:
        """Current active session ID"""
        return self._ws_client.current_session_id

    # Connection management
    async def connect(self) -> None:
        """Connect to server

        Establish WebSocket connection and prepare for speech synthesis.

        Raises:
            ConnectionError: Connection failed
            TimeoutError: Connection timeout
        """
        await self._ws_client.connect_websocket()
        logger.info(f"Connected to server: {self._ws_client.server_url}")

    async def close(self) -> None:
        """Close client

        Close all connections and resources.
        """
        try:
            # Close current session
            if self._current_session:
                await self._current_session.end()
                self._current_session = None

            # Close WebSocket connection
            await self._ws_client.close()

            # Close speaker manager
            await self.speaker.close()

        except Exception as e:
            logger.error(f"Error occurred while closing client: {e!s}")
        finally:
            logger.info("Client closed")

    # Advanced synthesis methods
    async def synthesize_text(
        self,
        text: str,
        config: SynthesisConfig,
        auto_session: bool = True,
    ) -> AsyncIterator[SynthesisResult]:
        """Single text streaming synthesis

        The simplest synthesis method that automatically manages session lifecycle.

        Args:
            text: Text to synthesize
            config: Synthesis configuration
            auto_session: Whether to automatically manage session

        Yields:
            SynthesisResult: Audio synthesis result

        Example:
            >>> config = SynthesisConfig(speaker_id="my_speaker")
            >>> async for result in client.synthesize_text("Hello World", config):
            ...     with open(f"audio_{result.chunk_index}.wav", "wb") as f:
            ...         f.write(result.audio_data)
        """
        validate_text_content(text)

        if auto_session:
            async with self.create_session() as session:
                # For auto session we don't persist config across calls
                async for result in session.synthesize_text(text, config):
                    yield result
        else:
            if not self._current_session:
                raise InvalidStateError("No active session, please create a session first or enable auto_session")
            # Bind or validate session config
            self._bind_or_validate_session_config(config)

            async for result in self._current_session.synthesize_text(text, config):
                yield result

    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        config: SynthesisConfig,
        auto_session: bool = True,
    ) -> AsyncIterator[SynthesisResult]:
        """Text stream synthesis

        Process async text streams for real-time synthesis.

        Args:
            text_stream: Async text stream
            config: Synthesis configuration
            auto_session: Whether to automatically manage session

        Yields:
            SynthesisResult: Audio synthesis result

        Example:
            >>> async def text_generator():
            ...     for sentence in sentences:
            ...         yield sentence
            ...         await asyncio.sleep(0.5)
            >>>
            >>> config = SynthesisConfig(speaker_id="my_speaker")
            >>> async for result in client.synthesize_stream(text_generator(), config):
            ...     play_audio(result.audio_data)
        """
        if auto_session:
            async with self.create_session() as session:
                async for result in session.synthesize_stream(text_stream, config):
                    yield result
        else:
            if not self._current_session:
                raise InvalidStateError("No active session, please create a session first or enable auto_session")
            self._bind_or_validate_session_config(config)

            async for result in self._current_session.synthesize_stream(text_stream, config):
                yield result

    async def collect_audio(
        self,
        text: str,
        config: SynthesisConfig,
        auto_session: bool = True,
    ) -> bytes:
        """Collect complete audio data

        Synthesize text and return complete audio data.

        Args:
            text: Text to synthesize
            config: Synthesis configuration
            auto_session: Whether to automatically manage session

        Returns:
            Complete audio data

        Example:
            >>> config = SynthesisConfig(speaker_id="my_speaker")
            >>> audio_data = await client.collect_audio("Hello World", config)
            >>> with open("output.wav", "wb") as f:
            ...     f.write(audio_data)
        """
        audio_chunks = []

        async for result in self.synthesize_text(text, config, auto_session):
            audio_chunks.append(result.audio_data)

        if not audio_chunks:
            return b""
        if len(audio_chunks) == 1:
            return audio_chunks[0]

        return merge_audio_chunks(audio_chunks, config.output_format)

    # Session management
    @asynccontextmanager
    async def create_session(self) -> AsyncIterator[StreamSession]:
        """Create and manage session context manager

        Automatically create, manage and cleanup sessions.

        Yields:
            StreamSession: Streaming synthesis session

        Example:
            >>> async with client.create_session() as session:
            ...     config = SynthesisConfig(speaker_id="my_speaker")
            ...     async for result in session.synthesize_text("Hello", config):
            ...         process_audio(result.audio_data)
        """
        if not self.is_connected:
            raise InvalidStateError("Client not connected, please call connect() first")

        session = None
        try:
            session = StreamSession(self._ws_client)
            await session.start()
            self._current_session = session
            yield session
        finally:
            if session:
                await session.end()
            self._current_session = None
            # Clear session config after auto-managed session ends
            self._session_config = None

    async def start_manual_session(self) -> str:
        """Start session manually

        Create a session and return session ID, requires manual session lifecycle management.

        Returns:
            Session ID

        Example:
            >>> session_id = await client.start_manual_session()
            >>> try:
            ...     # Use session for synthesis
            ...     pass
            >>> finally:
            ...     await client.end_manual_session()
        """
        if not self.is_connected:
            raise InvalidStateError("Client not connected, please call connect() first")

        if self._current_session:
            raise InvalidStateError("Active session exists, please end current session first")

        session = StreamSession(self._ws_client)
        session_id = await session.start()
        self._current_session = session
        return session_id

    async def end_manual_session(self) -> None:
        """End session manually"""
        if not self._current_session:
            raise InvalidStateError("No active session")

        await self._current_session.end()
        self._current_session = None

    # Event callbacks
    def set_audio_chunk_handler(self, handler: AudioStreamHandler) -> None:
        """Set audio chunk handler

        Args:
            handler: Audio chunk processing function

        Example:
            >>> async def on_audio_chunk(result: SynthesisResult):
            ...     print(f"Received audio chunk: {len(result.audio_data)} bytes")
            >>>
            >>> client.set_audio_chunk_handler(on_audio_chunk)
        """
        self._audio_chunk_handler = handler
        self._ws_client.set_audio_chunk_callback(handler)

    def set_synthesis_complete_handler(self, handler: SynthesisCompleteHandler) -> None:
        """Set synthesis complete handler

        Args:
            handler: Synthesis complete processing function

        Example:
            >>> async def on_synthesis_complete(session_id: str):
            ...     print(f"Synthesis complete for session: {session_id}")
            >>>
            >>> client.set_synthesis_complete_handler(on_synthesis_complete)
        """
        self._synthesis_complete_handler = handler
        self._ws_client.set_synthesis_complete_callback(handler)

    def set_error_handler(self, handler: ErrorHandler) -> None:
        """Set error handler

        Args:
            handler: Error processing function

        Example:
            >>> async def on_error(error: CosyVoiceError):
            ...     print(f"Error occurred: {error}")
            >>>
            >>> client.set_error_handler(on_error)
        """
        self._error_handler = handler
        self._ws_client.set_error_callback(handler)

    # Convenience methods
    async def quick_synthesize(
        self,
        text: str,
        speaker_prompt_text: str,
        speaker_audio_file: str | Path,
        speed: float = 1.0,
        output_file: str | Path | None = None,
        speaker_id: str | None = None,
    ) -> bytes:
        """Quick synthesis

        Convenience method to create speaker, synthesize speech and return audio data in one call.
        The created speaker will be retained for future use.

        Args:
            text: Text to synthesize
            speaker_prompt_text: Speaker reference text
            speaker_audio_file: Speaker reference audio file
            speed: Speech speed
            output_file: Optional output file path
            speaker_id: Optional speaker ID, will generate unique ID if not provided

        Returns:
            Audio data

        Example:
            >>> audio = await client.quick_synthesize(
            ...     text="Hello World",
            ...     speaker_prompt_text="Reference text",
            ...     speaker_audio_file="voice.wav",
            ...     output_file="output.wav"
            ... )
        """
        # Generate unique speaker ID if not provided
        if speaker_id is None:
            speaker_id = f"quick_{uuid.uuid4().hex[:8]}"

        # Check if speaker already exists, create if not
        if not await self.speaker.exists(speaker_id):
            await self.speaker.create(
                prompt_text=speaker_prompt_text,
                zero_shot_spk_id=speaker_id,
                prompt_audio_path=str(speaker_audio_file),
            )
            logger.info(f"Created speaker: {speaker_id}")
        else:
            logger.info(f"Using existing speaker: {speaker_id}")

        # Synthesize speech
        config = SynthesisConfig(
            speaker_id=speaker_id,
            speed=speed,
        )

        audio_data = await self.collect_audio(text, config)

        # Save file (optional)
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"Audio saved to: {output_path}")

        return audio_data

    # Context manager support
    async def __aenter__(self) -> 'StreamClient':
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    # Internal helpers
    def _bind_or_validate_session_config(self, config: SynthesisConfig) -> None:
        """Bind the first config to a manual session and validate subsequent ones are compatible.

        A session MUST NOT be reused with different core audio parameters because server-side
        synthesis context (voice embedding, codec pipeline) is fixed at session creation.

        Enforced immutable fields:
            speaker_id, mode, output_format, sample_rate, bit_rate, compression_level
        """
        if self._session_config is None:
            self._session_config = config
            return
        base = self._session_config
        if any([
            base.speaker_id != config.speaker_id,
            base.mode != config.mode,
            base.output_format != config.output_format,
            base.sample_rate != config.sample_rate,
            base.bit_rate != config.bit_rate,
            base.compression_level != config.compression_level,
        ]):
            raise InvalidStateError(
                "Current session was created with a different synthesis configuration; "
                "please end the session before using a new config or enable auto_session."
            )


# Convenience factory functions
async def create_client(
    server_url: str | None = None,
    **kwargs: Any
) -> StreamClient:
    """Create and connect client

    Args:
        server_url: Server URL, will load from environment variable COSYVOICE_BASE_URL if not provided
        **kwargs: Other parameters passed to StreamClient constructor

    Returns:
        Connected StreamClient instance

    Example:
        >>> client = await cosyvoice.create_client("wss://api.example.com")
        >>> try:
        ...     # Use the client
        ...     pass
        >>> finally:
        ...     await client.close()
    """
    client = StreamClient(server_url=server_url, **kwargs)
    await client.connect()
    return client


# Convenient context manager factory function
@asynccontextmanager
async def connect_client(server_url: str | None = None, **kwargs: Any) -> AsyncIterator[StreamClient]:
    """Create client context manager

    Args:
        server_url: Server URL, will load from environment variable COSYVOICE_BASE_URL if not provided
        **kwargs: Other parameters passed to StreamClient constructor

    Yields:
        StreamClient: Connected client instance

    Example:
        >>> async with cosyvoice.connect_client() as client:
        ...     config = cosyvoice.SynthesisConfig(speaker_id="speaker_1")
        ...     audio = await client.collect_audio("Hello World", config)
    """
    client = None
    try:
        client = StreamClient(server_url=server_url, **kwargs)
        await client.connect()
        yield client
    finally:
        if client:
            await client.close()
