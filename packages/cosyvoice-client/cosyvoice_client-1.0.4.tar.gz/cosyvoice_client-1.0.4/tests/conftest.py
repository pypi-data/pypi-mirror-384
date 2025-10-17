"""测试配置和共享 fixtures"""

# Try to load .env file for testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from collections.abc import AsyncGenerator

import pytest

import cosyvoice
from cosyvoice.models.enums import AudioFormat, SynthesisMode
from cosyvoice.models.synthesis import SynthesisConfig


@pytest.fixture
def test_server_url() -> str:
    """测试服务器 URL"""
    return "wss://test.cosyvoice.com"


@pytest.fixture
def synthesis_config() -> SynthesisConfig:
    """测试合成配置"""
    return SynthesisConfig(
        speaker_id="test_speaker",
        mode=SynthesisMode.ZERO_SHOT,
        speed=1.0,
        output_format=AudioFormat.WAV,
    )


@pytest.fixture
async def mock_client(test_server_url: str) -> AsyncGenerator[cosyvoice.StreamClient, None]:
    """模拟客户端"""
    client = cosyvoice.StreamClient(test_server_url)

    # 模拟连接状态
    client._ws_client._state = cosyvoice.ClientState.CONNECTED

    yield client

    # 清理
    await client.close()


@pytest.fixture
def sample_audio_data() -> bytes:
    """示例音频数据"""
    # 生成简单的 WAV 格式音频数据
    import io
    import wave

    import numpy as np

    # 生成 1 秒 16kHz 的正弦波
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0  # A4 音符

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(frequency * 2 * np.pi * t)

    # 转换为 16-bit PCM
    audio_data = (wave_data * 32767).astype(np.int16)

    # 创建 WAV 文件
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return buffer.getvalue()


@pytest.fixture
def sample_text() -> str:
    """示例文本"""
    return "这是一个测试文本。"


@pytest.fixture
def test_speaker_id() -> str:
    """测试音色ID"""
    return "test_speaker_001"


@pytest.fixture
def sample_prompt_text() -> str:
    """示例参考文本"""
    return "希望你以后能够做的比我还好呦。"


# 异步测试标记
pytestmark = pytest.mark.asyncio
