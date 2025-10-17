"""Basic Speech Synthesis Example

Demonstrates how to use CosyVoice Python SDK for basic speech synthesis.
"""

import asyncio
import logging
from pathlib import Path

import cosyvoice
from cosyvoice.utils.audio import merge_audio_chunks, write_wav_file

# Try to load .env file for development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables only")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_audio_with_format_conversion(audio_data: bytes, output_path: Path,
                                    audio_format: cosyvoice.AudioFormat,
                                    sample_rate: int = 22050) -> Path:
    """Save audio data, automatically convert PCM to WAV if needed

    Args:
        audio_data: Audio data bytes
        output_path: Output file path
        audio_format: Audio format type
        sample_rate: Sample rate in Hz

    Returns:
        Actual saved file path
    """
    output_path.parent.mkdir(exist_ok=True)

    if audio_format == cosyvoice.AudioFormat.PCM:
        # Convert PCM to WAV for better compatibility
        wav_path = output_path.with_suffix('.wav')
        write_wav_file(audio_data, wav_path, sample_rate)
        logger.info(f"PCM audio converted to WAV and saved to: {wav_path} ({len(audio_data)} bytes)")
        return wav_path
    else:
        # Save other formats directly
        with open(output_path, "wb") as f:
            f.write(audio_data)
        logger.info(f"Audio saved to: {output_path} ({len(audio_data)} bytes)")
        return output_path



async def basic_synthesis_example():
    """Basic speech synthesis example"""
    # Get configuration from environment variables

    # Connect to server
    async with cosyvoice.connect_client() as client:
        logger.info("Connected to CosyVoice server")

        # 1. Create speaker
        logger.info("Creating speaker...")
        speaker_id = "demo_speaker_001"

        # Check if speaker already exists
        # if await client.speaker.exists(speaker_id):
        #     logger.info(f"Speaker {speaker_id} already exists, using it directly")
        #     speaker_info = await client.speaker.get_info(speaker_id)
        # else:
        #     # Create new speaker
        #     speaker_info = await client.speaker.create(
        #         prompt_text="I hope you will do better than me in the future.",
        #         zero_shot_spk_id=speaker_id,
        #         prompt_audio_path="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
        #     )
        #     logger.info(f"Speaker created successfully: {speaker_id}")

        # speaker_id = speaker_info.zero_shot_spk_id

        # 2. Configure synthesis parameters
        config = cosyvoice.SynthesisConfig(
            speaker_id=speaker_id,
            mode=cosyvoice.SynthesisMode.ZERO_SHOT,
            speed=1.2,  # Speech speed 1.2x
            output_format=cosyvoice.AudioFormat.WAV,
            sample_rate=22050  # Output sample rate
        )

        # 3. Method 1: Collect complete audio
        logger.info("Synthesizing speech...")
        text = "Hello, this is a demonstration of CosyVoice Python SDK. Welcome to use our speech synthesis service!"

        audio_data = await client.collect_audio(text, config)

        # Save audio file
        output_file = Path("output") / "basic_synthesis.wav"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, "wb") as f:
            f.write(audio_data)

        logger.info(f"Audio saved to: {output_file}")
        logger.info(f"Audio size: {len(audio_data)} bytes")

        # Test different output formats
        logger.info("Testing different output formats...")

        # Test PCM format
        pcm_config = cosyvoice.SynthesisConfig(
            speaker_id=speaker_id,
            mode=cosyvoice.SynthesisMode.ZERO_SHOT,
            speed=1.0,
            output_format=cosyvoice.AudioFormat.PCM,
            sample_rate=22050
        )

        pcm_audio = await client.collect_audio("This is PCM format test.", pcm_config)
        pcm_output = Path("output") / "test_pcm.pcm"
        # Use new save function, PCM will be auto-converted to WAV
        save_audio_with_format_conversion(
            pcm_audio, pcm_output, cosyvoice.AudioFormat.PCM, 22050
        )

        # Test MP3 format
        mp3_config = cosyvoice.SynthesisConfig(
            speaker_id=speaker_id,
            mode=cosyvoice.SynthesisMode.ZERO_SHOT,
            speed=1.0,
            output_format=cosyvoice.AudioFormat.MP3,
            sample_rate=22050,
            bit_rate=128000  # 128kbps
        )

        mp3_audio = await client.collect_audio("This is MP3 format test.", mp3_config)
        mp3_output = Path("output") / "test_mp3.mp3"
        with open(mp3_output, "wb") as f:
            f.write(mp3_audio)
        logger.info(f"MP3 audio saved to: {mp3_output} ({len(mp3_audio)} bytes)")

        logger.info("Multi-format synthesis test completed")


async def streaming_synthesis_example():
    """Streaming speech synthesis example"""

    async with cosyvoice.connect_client() as client:
        logger.info("Connected to CosyVoice server")

        # Use existing speaker (assuming it's already created)
        config = cosyvoice.SynthesisConfig(
            speaker_id="demo_speaker_001",
            mode=cosyvoice.SynthesisMode.ZERO_SHOT,
            speed=1.0
        )

        # 4. Method 2: Process audio chunks in streaming mode
        logger.info("Starting streaming synthesis...")

        text = "This is an example of streaming synthesis. We can get audio data in real-time and process it."
        audio_chunks = []

        async for result in client.synthesize_text(text, config):
            logger.info(f"Received audio chunk {result.chunk_index}: {len(result.audio_data)} bytes")
            audio_chunks.append(result.audio_data)

            # Here you can play or process audio chunks in real-time
            # For example: player.play(result.audio_data)

        # Merge all audio chunks using the proper audio merge function
        complete_audio = merge_audio_chunks(audio_chunks, config.output_format)

        # Save complete audio
        output_file = Path("output") / "streaming_synthesis.wav"
        with open(output_file, "wb") as f:
            f.write(complete_audio)

        logger.info(f"Streaming synthesis completed, audio saved to: {output_file}")


async def text_stream_synthesis_example():
    """Text stream synthesis example"""

    async with cosyvoice.connect_client() as client:
        logger.info("Connected to CosyVoice server")

        config = cosyvoice.SynthesisConfig(
            speaker_id="demo_speaker_001",
            mode=cosyvoice.SynthesisMode.ZERO_SHOT
        )

        # 5. Text stream synthesis
        async def text_generator():
            """Simulate real-time text stream"""
            sentences = [
                "Welcome to use CosyVoice speech synthesis service.",
                "We support multiple languages and voices.",
                "High-quality speech synthesis can be achieved.",
                "Hope you enjoy using it!"
            ]

            for sentence in sentences:
                logger.info(f"Sending text: {sentence}")
                yield sentence
                await asyncio.sleep(1.0)  # Simulate real-time input delay

        logger.info("Starting text stream synthesis...")
        all_audio_data = []

        async for result in client.synthesize_stream(text_generator(), config):
            logger.info(f"Received audio: text{result.text_index}, chunk{result.chunk_index}")
            all_audio_data.append(result.audio_data)

        # Save complete audio using proper audio merge function
        complete_audio = merge_audio_chunks(all_audio_data, config.output_format)
        output_file = Path("output") / "text_stream_synthesis.wav"

        with open(output_file, "wb") as f:
            f.write(complete_audio)

        logger.info(f"Text stream synthesis completed: {output_file}")


async def quick_synthesis_example():
    """Quick synthesis example (create speaker and synthesize in one step)"""
    async with cosyvoice.connect_client() as client:
        logger.info("Quick synthesis example")

        # 6. Quick synthesis (automatically create temporary speaker)
        audio_data = await client.quick_synthesize(
            text="This is a demonstration of quick synthesis, no manual speaker management needed.",
            speaker_prompt_text="I hope you will do better than me in the future.",
            speaker_audio_file="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav",
            speed=1.1,
            output_file="output/quick_synthesis.wav"
        )

        logger.info(f"Quick synthesis completed, audio size: {len(audio_data)} bytes")


async def error_handling_example():
    """Error handling example"""

    try:
        async with cosyvoice.connect_client() as client:
            # Set error handler
            async def on_error(error: cosyvoice.CosyVoiceError):
                logger.error(f"Error occurred: {error.error_code} - {error.message}")
                if error.details:
                    logger.error(f"Error details: {error.details}")

            client.set_error_handler(on_error)

            # Try to use non-existent speaker
            config = cosyvoice.SynthesisConfig(
                speaker_id="nonexistent_speaker"
            )

            async for _result in client.synthesize_text("Test text", config):
                logger.info("Received audio data")

    except cosyvoice.ConnectionError as e:
        logger.error(f"Connection error: {e}")
    except cosyvoice.SpeakerError as e:
        logger.error(f"Speaker error: {e}")
    except cosyvoice.SynthesisError as e:
        logger.error(f"Synthesis error: {e}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")


async def multi_format_synthesis_example():
    """Multi-format synthesis example - test WAV, PCM, MP3 formats"""

    async with cosyvoice.connect_client() as client:
        logger.info("Connected to CosyVoice server for multi-format testing")

        # Use existing speaker
        speaker_id = "demo_speaker_001"

        # Test data
        test_text = "This is a multi-format synthesis test to verify different audio output formats."

        # Test configurations for different formats
        format_configs = [
            {
                "name": "WAV",
                "config": cosyvoice.SynthesisConfig(
                    speaker_id=speaker_id,
                    mode=cosyvoice.SynthesisMode.ZERO_SHOT,
                    output_format=cosyvoice.AudioFormat.WAV,
                    sample_rate=22050,
                    speed=1.0
                ),
                "extension": "wav"
            },
            {
                "name": "PCM",
                "config": cosyvoice.SynthesisConfig(
                    speaker_id=speaker_id,
                    mode=cosyvoice.SynthesisMode.ZERO_SHOT,
                    output_format=cosyvoice.AudioFormat.PCM,
                    sample_rate=22050,
                    speed=1.0
                ),
                "extension": "pcm"
            },
            {
                "name": "MP3_128k",
                "config": cosyvoice.SynthesisConfig(
                    speaker_id=speaker_id,
                    mode=cosyvoice.SynthesisMode.ZERO_SHOT,
                    output_format=cosyvoice.AudioFormat.MP3,
                    sample_rate=22050,
                    bit_rate=128000,  # 128kbps
                    speed=1.0
                ),
                "extension": "mp3"
            },
            {
                "name": "MP3_192k",
                "config": cosyvoice.SynthesisConfig(
                    speaker_id=speaker_id,
                    mode=cosyvoice.SynthesisMode.ZERO_SHOT,
                    output_format=cosyvoice.AudioFormat.MP3,
                    sample_rate=44100,
                    bit_rate=192000,  # 192kbps
                    speed=1.1
                ),
                "extension": "mp3"
            }
        ]

        # Test each format
        for format_info in format_configs:
            logger.info(f"Testing {format_info['name']} format...")

            try:
                # Synthesize audio
                audio_data = await client.collect_audio(test_text, format_info["config"])

                # Save file using the new function
                output_file = Path("output") / f"multi_format_{format_info['name'].lower()}.{format_info['extension']}"
                actual_file = save_audio_with_format_conversion(
                    audio_data,
                    output_file,
                    format_info["config"].output_format,
                    format_info["config"].sample_rate
                )

                logger.info(f"{format_info['name']} format test completed:")
                logger.info(f"  - File: {actual_file}")
                logger.info(f"  - Size: {len(audio_data)} bytes")
                logger.info(f"  - Sample rate: {format_info['config'].sample_rate} Hz")
                if hasattr(format_info['config'], 'bit_rate') and format_info['config'].bit_rate:
                    logger.info(f"  - Bit rate: {format_info['config'].bit_rate // 1000} kbps")

            except Exception as e:
                logger.error(f"Error testing {format_info['name']} format: {e}")

        logger.info("Multi-format synthesis testing completed")


if __name__ == "__main__":
    # Run examples (choose one)

    # Basic synthesis
    asyncio.run(basic_synthesis_example())

    # Multi-format synthesis test
    asyncio.run(multi_format_synthesis_example())

    # Streaming synthesis
    asyncio.run(streaming_synthesis_example())

    # Text stream synthesis
    asyncio.run(text_stream_synthesis_example())

    # Quick synthesis (requires server speaker management support)
    asyncio.run(quick_synthesis_example())

    # Error handling
    asyncio.run(error_handling_example())

    print("All examples completed!")
