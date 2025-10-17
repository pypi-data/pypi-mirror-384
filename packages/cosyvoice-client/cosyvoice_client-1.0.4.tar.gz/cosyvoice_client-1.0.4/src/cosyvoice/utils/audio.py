"""Audio processing utilities

Provides audio data processing, format conversion and other functionalities.
"""

import io
import logging
import wave
from pathlib import Path

import numpy as np

from ..models.enums import AudioFormat
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


def read_audio_file(file_path: str | Path) -> tuple[np.ndarray, int]:
    """Read audio file

    Args:
        file_path: Audio file path

    Returns:
        Tuple of audio data and sample rate (audio_data, sample_rate)

    Raises:
        ValidationError: File read failed
    """
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"Audio file does not exist: {file_path}")

    try:
        if path.suffix.lower() == '.wav':
            return _read_wav_file(path)
        else:
            raise ValidationError(f"Unsupported audio format: {path.suffix}")
    except Exception as e:
        raise ValidationError(f"Failed to read audio file: {e!s}") from e


def _read_wav_file(file_path: Path) -> tuple[np.ndarray, int]:
    """Read WAV file"""
    with wave.open(str(file_path), 'rb') as wav_file:
        # Get audio parameters
        frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()

        # Read audio data
        audio_bytes = wav_file.readframes(frames)

        # Convert to numpy array with proper typing
        if sample_width == 1:
            audio_data = np.frombuffer(audio_bytes, dtype=np.uint8)
        elif sample_width == 2:
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
        elif sample_width == 4:
            audio_data = np.frombuffer(audio_bytes, dtype=np.int32)
        else:
            raise ValidationError(f"Unsupported sample width: {sample_width}")

        # Handle multi-channel
        if channels > 1:
            audio_data = audio_data.reshape(-1, channels)
            # Convert to mono (take average)
            audio_data = np.mean(audio_data, axis=1)

        # Normalize to [-1, 1] based on original sample width
        if sample_width == 1:
            normalized_data = (audio_data.astype(np.float64) - 128) / 128
        elif sample_width == 2:
            normalized_data = audio_data.astype(np.float64) / 32768
        elif sample_width == 4:
            normalized_data = audio_data.astype(np.float64) / 2147483648
        else:
            normalized_data = audio_data.astype(np.float64)

        return normalized_data, sample_rate


def write_wav_file(
    audio_data: np.ndarray | bytes,
    file_path: str | Path,
    sample_rate: int = 22050,
    sample_width: int = 2
) -> None:
    """Write WAV file

    Args:
        audio_data: Audio data
        file_path: Output file path
        sample_rate: Sample rate
        sample_width: Sample width (bytes)
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(audio_data, np.ndarray):
        # Convert numpy array to bytes
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            # Float data, need to convert to integer
            if sample_width == 2:
                audio_data_int = (audio_data * 32767).astype(np.int16)
            elif sample_width == 1:
                audio_data_int = ((audio_data + 1) * 127.5).astype(np.uint8)
            else:
                raise ValidationError(f"Unsupported sample width: {sample_width}")
            audio_bytes = audio_data_int.tobytes()
        else:
            audio_bytes = audio_data.tobytes()
    else:
        audio_bytes = audio_data

    with wave.open(str(path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)


def combine_audio_chunks(audio_chunks: list[bytes]) -> bytes:
    """Combine audio chunks

    Args:
        audio_chunks: List of audio chunks

    Returns:
        Combined audio data
    """
    if not audio_chunks:
        return b''

    return b''.join(audio_chunks)


def get_audio_duration(audio_data: bytes, sample_rate: int, sample_width: int = 2) -> float:
    """Calculate audio duration

    Args:
        audio_data: Audio data
        sample_rate: Sample rate
        sample_width: Sample width (bytes)

    Returns:
        Audio duration in seconds
    """
    if not audio_data:
        return 0.0

    num_samples = len(audio_data) // sample_width
    return num_samples / sample_rate


def resample_audio(
    audio_data: np.ndarray,
    original_rate: int,
    target_rate: int
) -> np.ndarray:
    """Resample audio

    Args:
        audio_data: Original audio data
        original_rate: Original sample rate
        target_rate: Target sample rate

    Returns:
        Resampled audio data
    """
    if original_rate == target_rate:
        return audio_data

    # Simple linear interpolation resampling
    ratio = target_rate / original_rate
    new_length = int(len(audio_data) * ratio)

    # Use numpy's interpolation function
    indices = np.linspace(0, len(audio_data) - 1, new_length)
    resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)

    return resampled.astype(audio_data.dtype)  # type: ignore[no-any-return]


def validate_audio_data(audio_data: bytes, max_size: int = 10 * 1024 * 1024) -> bool:
    """Validate audio data

    Args:
        audio_data: Audio data
        max_size: Maximum file size (bytes)

    Returns:
        True if audio data is valid

    Raises:
        ValidationError: Audio data is invalid
    """
    if not audio_data:
        raise ValidationError("Audio data is empty")

    if len(audio_data) > max_size:
        raise ValidationError(f"Audio data too large: {len(audio_data)} bytes > {max_size} bytes")

    return True


def merge_audio_chunks(chunks: list[bytes], fmt: str | AudioFormat) -> bytes:
    """Merge multiple audio chunks according to target output format.

    Supports wav / mp3 / pcm. All logic uses Python stdlib only.

    Args:
        chunks: List of audio chunks to merge
        fmt: Audio format (AudioFormat enum or string)

    Returns:
        Merged audio data
    """
    if not chunks:
        return b""

    # Normalize format value
    format_value = fmt.value if isinstance(fmt, AudioFormat) else fmt.lower()
    if format_value == AudioFormat.WAV.value:
        return merge_wav_chunks(chunks)
    if format_value == AudioFormat.MP3.value:
        return merge_mp3_chunks(chunks)
    if format_value == AudioFormat.PCM.value:
        return merge_pcm_chunks(chunks)
    # Fallback: raw concatenation
    logger.debug("Unknown format %s, fallback to raw concatenation", format_value)
    return b"".join(chunks)


def merge_pcm_chunks(pcm_chunks: list[bytes]) -> bytes:
    """Merge raw PCM chunks (assumed identical format) by simple concatenation.

    Args:
        pcm_chunks: List of PCM audio chunks

    Returns:
        Merged PCM data
    """
    return b"".join(pcm_chunks)


def merge_mp3_chunks(mp3_chunks: list[bytes]) -> bytes:
    """Merge MP3 chunks.

    Strategy:
    - Keep the first ID3 tag (if present) and strip ID3 headers from subsequent chunks.
    - Concatenate remaining MP3 frame data.
    - Does not parse or re-write VBR headers (sufficient for streaming concatenation).

    Args:
        mp3_chunks: List of MP3 audio chunks

    Returns:
        Merged MP3 data
    """
    if not mp3_chunks:
        return b""

    def strip_id3(data: bytes) -> tuple[bytes, bytes]:
        if len(data) >= 10 and data[:3] == b"ID3":
            # ID3 header size uses synchsafe integers
            size_bytes = data[6:10]
            tag_size = (
                (size_bytes[0] & 0x7F) << 21 |
                (size_bytes[1] & 0x7F) << 14 |
                (size_bytes[2] & 0x7F) << 7 |
                (size_bytes[3] & 0x7F)
            )
            total = 10 + tag_size
            return data[:total], data[total:]
        return b"", data

    first = mp3_chunks[0]
    first_id3, first_rest = strip_id3(first)
    frames = [first_rest]

    skipped = 0
    for chunk in mp3_chunks[1:]:
        _, rest = strip_id3(chunk)  # discard subsequent ID3 (if any)
        if rest:
            frames.append(rest)
        else:
            skipped += 1
    if skipped:
        logger.debug("MP3 merge skipped %d empty chunks", skipped)
    return first_id3 + b"".join(frames)


def merge_wav_chunks(wav_chunks: list[bytes]) -> bytes:
    """Merge multiple complete WAV chunks (same audio format) into one WAV file using only stdlib.

    Algorithm:
    1. Parse each chunk via wave module (wrap bytes with BytesIO).
    2. Use the first valid chunk's format (channels, sample width, frame rate, compression) as baseline.
    3. Validate following chunks match baseline (ignore compression name differences). Mismatches are skipped.
    4. Concatenate raw frames and write a fresh WAV header (avoids duplicating headers).
    5. If no valid frames found, return empty bytes.

    Args:
        wav_chunks: List of independent complete WAV file bytes.

    Returns:
        bytes: Single merged WAV file bytes.
    """
    if not wav_chunks:
        return b""

    valid_params: tuple[int, int, int, str, str] | None = None
    frames_list: list[bytes] = []
    skipped = 0

    for idx, data in enumerate(wav_chunks):
        if not data or len(data) < 44:  # 基本 header 长度判断
            skipped += 1
            continue
        try:
            with wave.open(io.BytesIO(data), "rb") as wf:
                params = (wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getcomptype(), wf.getcompname())
                if valid_params is None:
                    valid_params = params
                else:
                    if params[:4] != valid_params[:4]:  # Compare first 4 params; compname difference ignored
                        logger.warning(
                            "Skip chunk %d due to format mismatch: %s != %s", idx, params[:4], valid_params[:4]
                        )
                        skipped += 1
                        continue
                frames = wf.readframes(wf.getnframes())
                if frames:
                    frames_list.append(frames)
                else:
                    skipped += 1
        except wave.Error as e:  # 非法 wav
            logger.warning("Skip invalid WAV chunk %d: %s", idx, e)
            skipped += 1
        except Exception as e:  # 其它异常
            logger.warning("Skip chunk %d due to unexpected error: %s", idx, e)
            skipped += 1

    if valid_params is None or not frames_list:  # 没有任何有效帧
        return b""

    nch, sampwidth, framerate, comptype, compname = valid_params

    # 写入到内存 buffer
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as out_wf:
        out_wf.setnchannels(nch)
        out_wf.setsampwidth(sampwidth)
        out_wf.setframerate(framerate)
        out_wf.setcomptype(comptype, compname)
        for frames in frames_list:
            out_wf.writeframes(frames)

    merged = out_buf.getvalue()
    if skipped:
        logger.debug("Merged WAV chunks: %d used, %d skipped", len(frames_list), skipped)
    return merged
