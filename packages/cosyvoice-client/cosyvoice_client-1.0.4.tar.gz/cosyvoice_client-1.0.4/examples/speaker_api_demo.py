#!/usr/bin/env python3
"""Speaker API JSON request examples

Demonstrates how to construct JSON requests for speaker management APIs
using the updated data models that match the server API.
"""

import json
import sys
from pathlib import Path

# Try to load .env file for development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from cosyvoice.models.speaker import (  # noqa: E402
    CreateSpeakerRequest,
    UpdateSpeakerRequest,
)


def demo_create_speaker_json():
    """Demonstrate CreateSpeakerRequest JSON serialization"""
    print("=== Create Speaker JSON POST Example ===")

    # Create request with test parameters
    create_request = CreateSpeakerRequest(
        prompt_text="I hope you can do even better than me in the future.",
        zero_shot_spk_id="test_speaker_001",
        prompt_audio_path="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
    )

    # Convert to JSON for POST request
    json_data = create_request.model_dump()
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    print("POST /speakers")
    print("Content-Type: application/json")
    print("Body:")
    print(json_str)
    print()

def demo_create_speaker_auto_id_json():
    """Demonstrate CreateSpeakerRequest with auto-generated ID"""
    print("=== Create Speaker with Auto-generated ID ===")

    # Create request without speaker ID (will be auto-generated)
    create_request = CreateSpeakerRequest(
        prompt_text="希望你以后能够做的比我还好呦。",
        prompt_audio_path="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
    )

    json_data = create_request.model_dump()
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    print("POST /speakers")
    print("Content-Type: application/json")
    print("Body:")
    print(json_str)
    print()

def demo_update_speaker_json():
    """Demonstrate UpdateSpeakerRequest JSON serialization"""
    print("=== Update Speaker JSON PUT Example ===")

    # Update request
    update_request = UpdateSpeakerRequest(
        prompt_text="希望你以后能够做的比我还好呦。",
        prompt_audio_path="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
    )

    json_data = update_request.model_dump()
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    print("PUT /speakers/{zero_shot_spk_id}")
    print("Content-Type: application/json")
    print("Body:")
    print(json_str)
    print()

def demo_partial_update_json():
    """Demonstrate partial update (text only)"""
    print("=== Partial Update (Text Only) ===")

    update_request = UpdateSpeakerRequest(
        prompt_text="New prompt text"
    )

    json_data = update_request.model_dump()
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    print("PUT /speakers/{zero_shot_spk_id}")
    print("Content-Type: application/json")
    print("Body:")
    print(json_str)
    print()

def demo_expected_responses():
    """Show expected response formats"""
    print("=== Expected Response Formats ===")

    # Success response example
    success_response = {
        "is_success": True,
        "speaker_info": {
            "zero_shot_spk_id": "test_speaker_001",
            "prompt_text": "希望你以后能够做的比我还好呦。",
            "created_at": "2025-01-01T00:00:00",
            "audio_url": "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
        },
        "request_id": "req_12345"
    }

    print("Success Response:")
    print(json.dumps(success_response, indent=2, ensure_ascii=False))
    print()

    # Error response example
    error_response = {
        "is_success": False,
        "error": {
            "code": "SPEAKER_ALREADY_EXISTS",
            "message": "Speaker with this ID already exists",
            "details": {"speaker_id": "test_speaker_001"}
        },
        "request_id": "req_12346"
    }

    print("Error Response:")
    print(json.dumps(error_response, indent=2, ensure_ascii=False))
    print()

def main():
    """Run all demonstrations"""
    print("JSON POST Request Examples for Speaker Management\n")

    demo_create_speaker_json()
    demo_create_speaker_auto_id_json()
    demo_update_speaker_json()
    demo_partial_update_json()
    demo_expected_responses()

    print("✅ All JSON examples completed!")

if __name__ == "__main__":
    main()
