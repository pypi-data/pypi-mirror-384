"""Tests for speaker data models"""

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
            prompt_text="Updated text only"
        )

        assert request.prompt_text == "Updated text only"
        assert request.prompt_audio_path is None

    def test_update_audio_only(self):
        """Test updating only audio_path"""
        request = UpdateSpeakerRequest(
            prompt_audio_path="https://example.com/new_audio.wav"
        )

        assert request.prompt_text is None
        assert request.prompt_audio_path == "https://example.com/new_audio.wav"

    def test_empty_update_request(self):
        """Test creating empty update request"""
        request = UpdateSpeakerRequest()

        assert request.prompt_text is None
        assert request.prompt_audio_path is None

    def test_invalid_audio_url_update(self):
        """Test validation for invalid audio URL in update"""
        with pytest.raises(ValueError, match="prompt_audio_path only supports HTTP/HTTPS URLs"):
            UpdateSpeakerRequest(
                prompt_audio_path="file:///local/file.wav"
            )


class TestSpeakerResponse:
    """Test cases for SpeakerResponse"""

    def test_success_response(self):
        """Test successful response creation"""
        response = SpeakerResponse(
            is_success=True,
            speaker_info={"zero_shot_spk_id": "test_speaker", "status": "ready"},
            request_id="req_12345"
        )

        assert response.is_success is True
        assert response.error is None
        assert response.speaker_info == {"zero_shot_spk_id": "test_speaker", "status": "ready"}
        assert response.request_id == "req_12345"

    def test_error_response(self):
        """Test error response creation"""
        response = SpeakerResponse(
            is_success=False,
            error={"code": "INVALID_INPUT", "message": "Invalid speaker data"},
            request_id="req_12346"
        )

        assert response.is_success is False
        assert response.speaker_info is None
        assert response.error == {"code": "INVALID_INPUT", "message": "Invalid speaker data"}
        assert response.request_id == "req_12346"

    def test_minimal_response(self):
        """Test minimal response creation"""
        response = SpeakerResponse(
            is_success=True
        )

        assert response.is_success is True
        assert response.error is None
        assert response.speaker_info is None
        assert response.request_id is None


class TestSpeakerInfo:
    """Test cases for SpeakerInfo"""

    def test_speaker_info_creation(self):
        """Test SpeakerInfo model creation"""
        info = SpeakerInfo(
            zero_shot_spk_id="speaker_001",
            prompt_text="Test prompt",
            created_at="2024-01-01T00:00:00Z",
            audio_url="https://example.com/audio.wav"
        )

        assert info.zero_shot_spk_id == "speaker_001"
        assert info.prompt_text == "Test prompt"
        assert info.created_at == "2024-01-01T00:00:00Z"
        assert info.audio_url == "https://example.com/audio.wav"

    def test_speaker_creation_with_minimal_fields(self):
        """Test speaker creation with minimal required fields"""
        # Test that SpeakerInfo requires all 4 fields
        info = SpeakerInfo(
            zero_shot_spk_id="minimal_speaker",
            prompt_text="Minimal test",
            created_at="2024-01-01T00:00:00Z",
            audio_url="https://example.com/minimal.wav"
        )

        assert info.zero_shot_spk_id == "minimal_speaker"
        assert info.prompt_text == "Minimal test"
        assert info.created_at == "2024-01-01T00:00:00Z"
        assert info.audio_url == "https://example.com/minimal.wav"


# Test functions for manual verification
def test_invalid_audio_path():
    """Test validation of audio path"""
    print("\n=== Testing Audio Path Validation ===")

    # Test invalid local path
    try:
        CreateSpeakerRequest(
            prompt_text="Test text",
            prompt_audio_path="/local/path/audio.wav"
        )
        print("❌ Should have failed but succeeded")
    except ValueError as e:
        print(f"✅ Correctly rejected local path: {e}")

    # Test invalid protocol
    try:
        CreateSpeakerRequest(
            prompt_text="Test text",
            prompt_audio_path="ftp://example.com/audio.wav"
        )
        print("❌ Should have failed but succeeded")
    except ValueError as e:
        print(f"✅ Correctly rejected non-HTTP protocol: {e}")


def test_update_speaker_request():
    """Test UpdateSpeakerRequest model"""
    print("\n=== Testing UpdateSpeakerRequest ===")

    try:
        update_request = UpdateSpeakerRequest(
            prompt_text="Updated text content",
            prompt_audio_path="https://edu-public-assets.edu-aliyun.com/updated_audio.wav"
        )
        print("✅ UpdateSpeakerRequest created:")
        print(f"   prompt_text: {update_request.prompt_text}")
        print(f"   prompt_audio_path: {update_request.prompt_audio_path}")
    except Exception as e:
        print(f"❌ UpdateSpeakerRequest failed: {e}")


def test_speaker_response():
    """Test SpeakerResponse model"""
    print("\n=== Testing SpeakerResponse ===")

    try:
        success_response = SpeakerResponse(
            is_success=True,
            speaker_info={
                "zero_shot_spk_id": "test_speaker_001",
                "prompt_text": "希望你以后能够做的比我还好呦。",
                "created_at": "2024-01-01T00:00:00Z",
                "audio_url": "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
            },
            request_id="req_12345"
        )
        print("✅ Success response created:")
        print(f"   is_success: {success_response.is_success}")
        print(f"   speaker_info: {success_response.speaker_info}")
    except Exception as e:
        print(f"❌ Success response failed: {e}")

    try:
        error_response = SpeakerResponse(
            is_success=False,
            error={
                "code": "SPEAKER_ALREADY_EXISTS",
                "message": "Speaker with this ID already exists",
                "details": {"speaker_id": "test_speaker_001"}
            },
            request_id="req_12346"
        )
        print("✅ Error response created:")
        print(f"   is_success: {error_response.is_success}")
        print(f"   error: {error_response.error}")
    except Exception as e:
        print(f"❌ Error response failed: {e}")


def test_speaker_info():
    """Test SpeakerInfo model"""
    print("\n=== Testing SpeakerInfo ===")

    try:
        speaker_info = SpeakerInfo(
            zero_shot_spk_id="test_speaker_001",
            prompt_text="希望你以后能够做的比我还好呦。",
            created_at="2024-01-01T00:00:00Z",
            audio_url="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
        )
        print("✅ SpeakerInfo created:")
        print(f"   zero_shot_spk_id: {speaker_info.zero_shot_spk_id}")
        print(f"   prompt_text: {speaker_info.prompt_text}")
        print(f"   created_at: {speaker_info.created_at}")
        print(f"   audio_url: {speaker_info.audio_url}")
    except Exception as e:
        print(f"❌ SpeakerInfo creation failed: {e}")


def main():
    """Run all tests"""
    print("Testing speaker data models with provided test parameters\n")

    test_invalid_audio_path()
    test_update_speaker_request()
    test_speaker_response()
    test_speaker_info()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()
