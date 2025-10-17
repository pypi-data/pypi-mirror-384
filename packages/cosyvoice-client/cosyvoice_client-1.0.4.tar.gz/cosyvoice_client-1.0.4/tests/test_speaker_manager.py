"""Speaker Manager Tests"""

from unittest.mock import patch

import pytest

from cosyvoice.models.speaker import SpeakerInfo
from cosyvoice.speaker.manager import SpeakerManager
from cosyvoice.utils.exceptions import SpeakerError, ValidationError


class TestSpeakerManager:
    """Test speaker manager"""

    @pytest.fixture
    def speaker_manager(self, test_server_url: str) -> SpeakerManager:
        """Create speaker manager instance"""
        return SpeakerManager(test_server_url)

    @pytest.fixture
    def sample_speaker_info(self, test_speaker_id: str) -> SpeakerInfo:
        """Sample speaker info"""
        return SpeakerInfo(
            zero_shot_spk_id=test_speaker_id,
            prompt_text="Test reference text",
            created_at="2025-01-01T00:00:00",
            audio_url="https://example.com/audio.wav"
        )

    def test_manager_initialization(self, speaker_manager: SpeakerManager, test_server_url: str):
        """Test manager initialization"""
        assert speaker_manager.server_url.startswith(test_server_url.replace('wss://', 'https://'))
        assert speaker_manager.timeout == 30.0
        assert speaker_manager.max_retries == 3

    def test_invalid_server_url(self):
        """Test invalid server URL"""
        with pytest.raises(ValidationError):
            SpeakerManager("invalid-url")

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_create_speaker_success(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        test_speaker_id: str,
        sample_prompt_text: str
    ):
        """Test successful speaker creation"""
        # Mock the complete response data that _handle_response would return
        mock_response_data = {
            "is_success": True,
            "speaker_info": {
                "zero_shot_spk_id": test_speaker_id,
                "prompt_text": sample_prompt_text,
                "created_at": "2025-01-01T00:00:00",
                "audio_url": "https://example.com/audio.wav"
            }
        }

        # Mock _make_request to return the response data directly
        mock_request.return_value = mock_response_data

        # Execute creation
        result = await speaker_manager.create(
            prompt_text=sample_prompt_text,
            prompt_audio_path="https://example.com/audio.wav",
            zero_shot_spk_id=test_speaker_id
        )

        # Verify result
        assert result.zero_shot_spk_id == test_speaker_id
        assert result.prompt_text == sample_prompt_text

        # Verify method calls
        mock_request.assert_called_once()

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_create_speaker_failure(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        test_speaker_id: str,
        sample_prompt_text: str
    ):
        """Test speaker creation failure"""
        # Mock failure response data
        mock_response_data = {
            "is_success": False,
            "error": {"code": "INVALID_AUDIO", "message": "Unsupported audio format"}
        }

        # Mock _make_request to return the failure response
        mock_request.return_value = mock_response_data

        # Execute creation and verify exception
        with pytest.raises(SpeakerError) as exc_info:
            await speaker_manager.create(
                prompt_text=sample_prompt_text,
                prompt_audio_path="https://example.com/audio.wav",
                zero_shot_spk_id=test_speaker_id
            )

        assert "Unsupported audio format" in str(exc_info.value)

    async def test_create_speaker_invalid_params(
        self,
        speaker_manager: SpeakerManager
    ):
        """Test speaker creation parameter validation"""
        # Invalid prompt text
        with pytest.raises(ValidationError):
            await speaker_manager.create("", "https://example.com/audio.wav")

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_get_info_success(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        sample_speaker_info: SpeakerInfo
    ):
        """Test successful speaker info retrieval"""
        # Mock the response data directly
        mock_response_data = sample_speaker_info.model_dump()
        mock_request.return_value = mock_response_data

        # Execute retrieval
        result = await speaker_manager.get_info(sample_speaker_info.zero_shot_spk_id)

        # Verify result
        assert result.zero_shot_spk_id == sample_speaker_info.zero_shot_spk_id
        assert result.prompt_text == sample_speaker_info.prompt_text

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_get_info_not_found(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        test_speaker_id: str
    ):
        """Test speaker not found"""
        # Mock _make_request to raise SpeakerError for not found
        mock_request.side_effect = SpeakerError("Speaker not found: test_speaker_001")

        # Execute retrieval and verify exception
        with pytest.raises(SpeakerError) as exc_info:
            await speaker_manager.get_info(test_speaker_id)

        assert "Speaker not found" in str(exc_info.value)

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_update_speaker_success(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        test_speaker_id: str,
        sample_prompt_text: str
    ):
        """Test successful speaker update"""
        # Mock the response data directly
        mock_response_data = {
            "is_success": True,
            "speaker_info": {
                "zero_shot_spk_id": test_speaker_id,
                "prompt_text": "Updated text",
                "created_at": "2025-01-01T00:00:00",
                "audio_url": "https://example.com/new_audio.wav"
            }
        }

        mock_request.return_value = mock_response_data

        # Execute update
        result = await speaker_manager.update(
            zero_shot_spk_id=test_speaker_id,
            prompt_text="Updated text"
        )

        # Verify result
        assert result.zero_shot_spk_id == test_speaker_id
        assert result.prompt_text == "Updated text"

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_delete_speaker_success(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        test_speaker_id: str
    ):
        """Test successful speaker deletion"""
        # Mock the response data directly as a dictionary (what _make_request returns)
        mock_response_data = {
            "is_success": True
        }
        mock_request.return_value = mock_response_data

        # Execute deletion
        result = await speaker_manager.delete(test_speaker_id)

        # Verify result
        assert result is True

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_exists_true(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        sample_speaker_info: SpeakerInfo
    ):
        """Test speaker existence check - exists"""
        # Mock the response data
        mock_response_data = {
            "is_success": True,
            "speaker_info": sample_speaker_info.model_dump()
        }
        mock_request.return_value = mock_response_data

        result = await speaker_manager.exists(sample_speaker_info.zero_shot_spk_id)

        assert result is True

    @patch('cosyvoice.speaker.manager.SpeakerManager._make_request')
    async def test_exists_false(
        self,
        mock_request,
        speaker_manager: SpeakerManager,
        test_speaker_id: str
    ):
        """Test speaker existence check - does not exist"""
        # Mock SpeakerError to simulate speaker not found
        mock_request.side_effect = SpeakerError(
            "Speaker not found: test_speaker_001",
            error_code="SPEAKER_NOT_FOUND"
        )

        result = await speaker_manager.exists(test_speaker_id)

        assert result is False

    async def test_context_manager(self, speaker_manager: SpeakerManager):
        """Test context manager"""
        with patch.object(speaker_manager, 'close') as mock_close:
            mock_close.return_value = None

            async with speaker_manager as manager:
                assert manager is speaker_manager

            mock_close.assert_called_once()
