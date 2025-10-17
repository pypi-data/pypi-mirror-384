"""Client basic functionality tests"""

from unittest.mock import patch

import pytest

import cosyvoice
from cosyvoice.models.enums import ClientState
from cosyvoice.models.synthesis import SynthesisConfig
from cosyvoice.utils.exceptions import ConnectionError, InvalidStateError


class TestStreamClient:
    """Test StreamClient basic functionality"""

    def test_client_initialization(self, test_server_url: str):
        """Test client initialization"""
        client = cosyvoice.StreamClient(test_server_url)

        assert client._ws_client.server_url.startswith("wss://")
        assert client.state == ClientState.DISCONNECTED
        assert not client.is_connected
        assert client.current_session_id is None

    def test_invalid_server_url(self):
        """Test invalid server URL"""
        with pytest.raises(cosyvoice.ConfigurationError):
            cosyvoice.StreamClient("invalid-url")

    @patch('cosyvoice.stream.client.StreamWebSocketClient.connect_websocket')
    async def test_connect_success(self, mock_connect, test_server_url: str):
        """Test successful connection"""
        mock_connect.return_value = None

        client = cosyvoice.StreamClient(test_server_url)

        # Simulate connection state change
        client._ws_client._connection_state = ClientState.CONNECTED

        await client.connect()

        mock_connect.assert_called_once()
        assert client.is_connected

    @patch('cosyvoice.stream.client.StreamWebSocketClient.connect_websocket')
    async def test_connect_failure(self, mock_connect, test_server_url: str):
        """Test connection failure"""
        mock_connect.side_effect = ConnectionError("Connection failed")

        client = cosyvoice.StreamClient(test_server_url)

        with pytest.raises(ConnectionError):
            await client.connect()

    async def test_synthesize_text_without_connection(
        self,
        test_server_url: str,
        synthesis_config: SynthesisConfig,
        sample_text: str
    ):
        """Test synthesis without connection"""
        client = cosyvoice.StreamClient(test_server_url)

        with pytest.raises(InvalidStateError):
            async for _ in client.synthesize_text(sample_text, synthesis_config):
                pass

    @patch('cosyvoice.stream.session.StreamSession.synthesize_text')
    @patch('cosyvoice.stream.session.StreamSession.start')
    @patch('cosyvoice.stream.session.StreamSession.end')
    async def test_synthesize_text_with_auto_session(
        self,
        mock_end,
        mock_start,
        mock_synthesize,
        mock_client,
        synthesis_config: SynthesisConfig,
        sample_text: str,
        sample_audio_data: bytes
    ):
        """Test text synthesis with automatic session management"""
        # Mock connection state
        mock_client._ws_client._connection_state = ClientState.CONNECTED

        # Mock session methods
        mock_start.return_value = "test_session_001"
        mock_end.return_value = None

        # Mock synthesis result
        from datetime import datetime

        from cosyvoice.models.synthesis import SynthesisResult

        mock_result = SynthesisResult(
            audio_data=sample_audio_data,
            session_id="test_session_001",
            text_index=1,
            chunk_index=1,
            metadata={},
            timestamp=datetime.now()
        )

        async def mock_synthesize_generator(*args, **kwargs):
            yield mock_result

        mock_synthesize.return_value = mock_synthesize_generator()

        # Execute synthesis
        results = []
        async for result in mock_client.synthesize_text(sample_text, synthesis_config):
            results.append(result)

        # Verify results
        assert len(results) == 1
        assert results[0].audio_data == sample_audio_data
        assert results[0].session_id == "test_session_001"

        # Verify session management
        mock_start.assert_called_once()
        mock_end.assert_called_once()

    async def test_collect_audio(
        self,
        mock_client,
        synthesis_config: SynthesisConfig,
        sample_text: str,
        sample_audio_data: bytes
    ):
        """Test collecting complete audio data"""
        # Mock connection state
        mock_client._ws_client._connection_state = ClientState.CONNECTED

        # Change config to PCM for simple concatenation testing
        from cosyvoice.models.enums import AudioFormat
        from cosyvoice.models.synthesis import SynthesisConfig

        pcm_config = SynthesisConfig(
            speaker_id=synthesis_config.speaker_id,
            mode=synthesis_config.mode,
            output_format=AudioFormat.PCM,  # Use PCM for simple byte concatenation
            speed=synthesis_config.speed
        )

        with patch.object(mock_client, 'synthesize_text') as mock_synthesize:
            # Mock synthesis results - use simple raw audio data that can be concatenated
            from datetime import datetime

            from cosyvoice.models.synthesis import SynthesisResult

            # Create simple raw audio chunks that can be concatenated
            chunk1 = b'\x01\x02\x03\x04'
            chunk2 = b'\x05\x06\x07\x08'

            results = [
                SynthesisResult(
                    audio_data=chunk1,
                    session_id="test_session",
                    text_index=1,
                    chunk_index=1,
                    metadata={},
                    timestamp=datetime.now()
                ),
                SynthesisResult(
                    audio_data=chunk2,
                    session_id="test_session",
                    text_index=1,
                    chunk_index=2,
                    metadata={},
                    timestamp=datetime.now()
                )
            ]

            async def mock_synthesize_generator(*args, **kwargs):
                for result in results:
                    yield result

            mock_synthesize.return_value = mock_synthesize_generator()

            # Execute collection with PCM config
            audio_data = await mock_client.collect_audio(sample_text, pcm_config)

            # Verify result - PCM chunks are simply concatenated
            assert audio_data == chunk1 + chunk2
            mock_synthesize.assert_called_once()

    async def test_context_manager(self, test_server_url: str):
        """Test context manager"""
        with (
            patch('cosyvoice.stream.client.StreamWebSocketClient.connect_websocket') as mock_connect,
            patch('cosyvoice.stream.client.StreamWebSocketClient.close') as mock_close
        ):
            mock_connect.return_value = None
            mock_close.return_value = None

            async with cosyvoice.StreamClient(test_server_url) as client:
                assert client is not None

            mock_connect.assert_called_once()
            mock_close.assert_called_once()


class TestFactoryFunctions:
    """Test factory functions"""

    @patch('cosyvoice.client.StreamClient.connect')
    async def test_create_client(self, mock_connect, test_server_url: str):
        """Test create_client factory function"""
        mock_connect.return_value = None

        client = await cosyvoice.create_client(test_server_url)

        assert isinstance(client, cosyvoice.StreamClient)
        mock_connect.assert_called_once()

        # Cleanup
        await client.close()

    @patch('cosyvoice.client.StreamClient.connect')
    @patch('cosyvoice.client.StreamClient.close')
    async def test_connect_client_context_manager(
        self,
        mock_close,
        mock_connect,
        test_server_url: str
    ):
        """Test connect_client context manager"""
        mock_connect.return_value = None
        mock_close.return_value = None

        async with cosyvoice.connect_client(test_server_url) as client:
            assert isinstance(client, cosyvoice.StreamClient)

        mock_connect.assert_called_once()
        mock_close.assert_called_once()
