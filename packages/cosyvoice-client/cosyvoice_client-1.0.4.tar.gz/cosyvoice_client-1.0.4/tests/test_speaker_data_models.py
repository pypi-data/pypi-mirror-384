"""Test cases for speaker data models"""

import pytest

from cosyvoice.models.speaker import (
    CreateSpeakerRequest,
    SpeakerInfo,
    SpeakerResponse,
    UpdateSpeakerRequest,
)


class TestCreateSpeakerRequest:
    """Test cases for CreateSpeakerRequest"""

    def test_create_with_test_parameters(self):
        """Test CreateSpeakerRequest with provided test parameters"""
        request = CreateSpeakerRequest(
            prompt_text="希望你以后能够做的比我还好呦。",
            zero_shot_spk_id="test_speaker_001",
            prompt_audio_path="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
        )

        assert request.prompt_text == "希望你以后能够做的比我还好呦。"
        assert request.zero_shot_spk_id == "test_speaker_001"
        assert request.prompt_audio_path == "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"

    def test_create_with_auto_generated_id(self):
        """Test CreateSpeakerRequest with auto-generated speaker ID"""
        request = CreateSpeakerRequest(
            prompt_audio_path="https://example.com/audio.wav"
        )

        assert request.zero_shot_spk_id is None
        assert request.prompt_text == "希望你以后能够做的比我还好呦。"

    def test_invalid_audio_path_local_file(self):
        """Test validation for local file paths (should fail)"""
        with pytest.raises(ValueError, match="prompt_audio_path only supports HTTP/HTTPS URLs"):
            CreateSpeakerRequest(
                prompt_audio_path="/local/path/audio.wav"
            )

    def test_invalid_speaker_id_format(self):
        """Test validation for invalid speaker ID format"""
        with pytest.raises(ValueError, match="Speaker ID can only contain"):
            CreateSpeakerRequest(
                zero_shot_spk_id="invalid@speaker!id",
                prompt_audio_path="https://example.com/audio.wav"
            )

    def test_valid_speaker_id_formats(self):
        """Test valid speaker ID formats"""
        valid_ids = ["speaker_001", "test-speaker", "TestSpeaker123", "speaker_test_001"]

        for speaker_id in valid_ids:
            request = CreateSpeakerRequest(
                zero_shot_spk_id=speaker_id,
                prompt_audio_path="https://example.com/audio.wav"
            )
            assert request.zero_shot_spk_id == speaker_id


class TestUpdateSpeakerRequest:
    """Test cases for UpdateSpeakerRequest"""

    def test_update_both_fields(self):
        """Test updating both prompt_text and audio_path"""
        request = UpdateSpeakerRequest(
            prompt_text="Updated text",
            prompt_audio_path="https://example.com/new_audio.wav"
        )

        assert request.prompt_text == "Updated text"
        assert request.prompt_audio_path == "https://example.com/new_audio.wav"

    def test_update_text_only(self):
        """Test updating only prompt_text"""
        request = UpdateSpeakerRequest(
            prompt_text="New text only"
        )

        assert request.prompt_text == "New text only"
        assert request.prompt_audio_path is None

    def test_update_audio_only(self):
        """Test updating only audio_path"""
        request = UpdateSpeakerRequest(
            prompt_audio_path="https://example.com/updated_audio.wav"
        )

        assert request.prompt_text is None
        assert request.prompt_audio_path == "https://example.com/updated_audio.wav"

    def test_invalid_audio_url(self):
        """Test validation for invalid audio URL"""
        with pytest.raises(ValueError, match="prompt_audio_path only supports HTTP/HTTPS URLs"):
            UpdateSpeakerRequest(
                prompt_audio_path="ftp://example.com/audio.wav"
            )


class TestSpeakerResponse:
    """Test cases for SpeakerResponse"""

    def test_success_response(self):
        """Test successful speaker response"""
        response = SpeakerResponse(
            is_success=True,
            speaker_info={
                "zero_shot_spk_id": "test_001",
                "prompt_text": "Test text",
                "created_at": "2025-01-01T00:00:00"
            },
            request_id="req_123"
        )

        assert response.is_success is True
        assert response.speaker_info["zero_shot_spk_id"] == "test_001"
        assert response.request_id == "req_123"
        assert response.error is None

    def test_error_response(self):
        """Test error speaker response"""
        response = SpeakerResponse(
            is_success=False,
            error={
                "code": "SPEAKER_NOT_FOUND",
                "message": "Speaker not found",
                "details": {"speaker_id": "missing_speaker"}
            },
            request_id="req_456"
        )

        assert response.is_success is False
        assert response.error["code"] == "SPEAKER_NOT_FOUND"
        assert response.speaker_info is None


class TestSpeakerInfo:
    """Test cases for SpeakerInfo"""

    def test_speaker_info_creation(self):
        """Test SpeakerInfo model creation with server response fields"""
        info = SpeakerInfo(
            zero_shot_spk_id="speaker_001",
            prompt_text="Test prompt",
            created_at="2025-01-01T00:00:00",
            audio_url="https://example.com/audio.wav"
        )

        assert info.zero_shot_spk_id == "speaker_001"
        assert info.prompt_text == "Test prompt"
        assert info.created_at == "2025-01-01T00:00:00"
        assert info.audio_url == "https://example.com/audio.wav"

    def test_speaker_info_with_test_parameters(self):
        """Test SpeakerInfo with provided test parameters"""
        info = SpeakerInfo(
            zero_shot_spk_id="test_speaker_001",
            prompt_text="希望你以后能够做的比我还好呦。",
            created_at="2025-01-01T00:00:00",
            audio_url="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
        )

        assert info.zero_shot_spk_id == "test_speaker_001"
        assert info.prompt_text == "希望你以后能够做的比我还好呦。"
        assert info.audio_url == "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
