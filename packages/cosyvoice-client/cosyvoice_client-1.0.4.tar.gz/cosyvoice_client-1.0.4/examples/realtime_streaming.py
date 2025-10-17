"""Real-time streaming speech synthesis example

Demonstrates real-time streaming TTS synthesis, suitable for real-time conversations, live broadcasts, etc.
Supports text stream input and audio stream output.
"""

import asyncio
import logging
import time
from pathlib import Path

# Try to load .env file for development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import cosyvoice

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealTimeAudioPlayer:
    """Simple real-time audio player (simulated)"""

    def __init__(self):
        self.total_played = 0
        self.start_time = None

    def start(self):
        """Start playback"""
        self.start_time = time.time()
        logger.info("Audio playback started")

    def play_chunk(self, audio_data: bytes):
        """Play audio chunk"""
        self.total_played += len(audio_data)
        logger.debug(f"Playing audio chunk: {len(audio_data)} bytes (total: {self.total_played} bytes)")

        # In a real application, send audio data to the audio output device here
        # e.g., using sounddevice, pyaudio, etc.

    def stop(self):
        """Stop playback"""
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info(f"Audio playback ended - duration: {duration:.2f}s, total bytes: {self.total_played} bytes")


class PerformanceMonitor:
    """Performance monitor"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset metrics"""
        self.start_time = None
        self.first_chunk_time = None
        self.total_chunks = 0
        self.total_audio_bytes = 0
        self.text_count = 0

    def start_synthesis(self):
        """Start synthesis"""
        self.start_time = time.time()
        logger.info("Starting performance monitoring")

    def record_audio_chunk(self, chunk_size: int):
        """Record audio chunk"""
        if self.first_chunk_time is None:
            self.first_chunk_time = time.time()
            ttfb = (self.first_chunk_time - self.start_time) * 1000
            logger.info(f"TTFB (first chunk latency): {ttfb:.1f}ms")

        self.total_chunks += 1
        self.total_audio_bytes += chunk_size

    def record_text(self):
        """Record text processing"""
        self.text_count += 1

    def get_stats(self) -> dict:
        """Get metrics"""
        if self.start_time is None:
            return {}

        total_time = time.time() - self.start_time
        ttfb = (self.first_chunk_time - self.start_time) * 1000 if self.first_chunk_time else 0

        return {
            "total_time": total_time,
            "ttfb_ms": ttfb,
            "total_chunks": self.total_chunks,
            "total_audio_bytes": self.total_audio_bytes,
            "text_count": self.text_count,
            "avg_chunk_size": self.total_audio_bytes / self.total_chunks if self.total_chunks > 0 else 0,
            "throughput_mbps": (self.total_audio_bytes * 8) / (total_time * 1_000_000) if total_time > 0 else 0,
        }


async def realtime_synthesis_with_events():
    """Real-time speech synthesis demonstrating iterator pattern

    This example demonstrates that high-level APIs like synthesize_stream()
    use iterator pattern for reliable result processing.
    Event handlers work at the WebSocket message level and are typically
    not triggered by high-level streaming APIs.
    """

    # Create monitor and player
    monitor = PerformanceMonitor()
    player = RealTimeAudioPlayer()

    async with cosyvoice.connect_client() as client:
        logger.info("Connected to CosyVoice server")

        # Configure synthesis parameters
        config = cosyvoice.SynthesisConfig(
            speaker_id="demo_speaker_001",
            mode=cosyvoice.SynthesisMode.ZERO_SHOT,
            speed=1.0,
            output_format=cosyvoice.AudioFormat.WAV
        )

        # Start monitoring
        monitor.start_synthesis()
        player.start()

        # Real-time text stream
        sentences = [
            "Welcome to CosyVoice real-time speech synthesis service.",
            "We support high-quality real-time speech generation.",
            "Can handle continuous text input.",
            "And provide low-latency audio output.",
            "Hope you enjoy using it!"
        ]

        async def text_stream():
            for i, sentence in enumerate(sentences):
                logger.info(f"Sending text {i+1}: {sentence}")
                monitor.record_text()
                yield sentence
                await asyncio.sleep(2.0)  # Simulate real-time input interval

        # Execute real-time streaming synthesis using iterator pattern
        logger.info("Starting real-time streaming synthesis with iterator pattern...")

        chunk_count = 0
        current_text_index = None

        async for result in client.synthesize_stream(text_stream(), config):
            chunk_count += 1
            monitor.record_audio_chunk(len(result.audio_data))
            player.play_chunk(result.audio_data)

            # Track when we move to a new text (indicates previous text is complete)
            if current_text_index is not None and result.text_index != current_text_index:
                logger.info(f"Text {current_text_index} synthesis completed")
            current_text_index = result.text_index

        # Final stats
        player.stop()
        perf_stats = monitor.get_stats()
        logger.info("Performance stats:")
        for key, value in perf_stats.items():
            logger.info(f"  {key}: {value}")

        logger.info(f"Total chunks processed: {chunk_count}")
        if current_text_index is not None:
            logger.info(f"Last text completed: {current_text_index}")
        logger.info("Real-time synthesis completed")

        logger.info("\nKEY INSIGHTS:")
        logger.info("- High-level streaming APIs use iterator pattern for reliable processing")
        logger.info("- Event handlers work at WebSocket level (lower-level message handling)")
        logger.info("- For most applications, use the iterator pattern for consistent results")


async def customer_service_simulation():
    """实时客服对话场景演示

    这个示例展示了如何使用 synthesize_stream 实现低延迟的实时客服对话:
    - 使用流式合成而不是 collect_audio 来降低首包延迟
    - 支持实时文本输入和音频流输出
    - 适合智能客服、实时翻译等场景
    """
    logger.info("=== 实时客服对话场景演示 ===")

    # 简单的音频播放器, 模拟实时播放
    class StreamingAudioPlayer:
        def __init__(self):
            self.is_playing = False
            self.total_audio_chunks = 0
            self.first_chunk_time = None

        async def play_audio_chunk(self, audio_data: bytes, text_index: int, chunk_index: int):
            """播放音频块"""
            if not self.is_playing:
                self.is_playing = True
                self.first_chunk_time = time.time()
                logger.info("🔊 开始播放音频")

            self.total_audio_chunks += 1
            # 这里应该将音频数据发送到音频输出设备
            # 例如: audio_output.write(audio_data)

        def get_latency_ms(self, start_time: float) -> float:
            """计算首包延迟"""
            if self.first_chunk_time:
                return (self.first_chunk_time - start_time) * 1000
            return 0

    async with cosyvoice.connect_client() as client:
        logger.info("已连接到 CosyVoice 服务器")

        # 配置客服音色
        config = cosyvoice.SynthesisConfig(
            speaker_id="demo_speaker_001",  # 使用默认测试音色
            mode=cosyvoice.SynthesisMode.ZERO_SHOT,
            speed=1.1,  # 略快的语速, 提高效率
            output_format=cosyvoice.AudioFormat.WAV
        )

        # 模拟客服对话场景
        customer_queries = [
            "您好, 请问有什么可以帮助您的吗?",
            "好的, 我来为您查询订单状态。",
            "您的订单已经发货, 预计明天下午送达。",
            "还有其他问题需要咨询吗?",
            "感谢您的来电, 祝您生活愉快!"
        ]

        # 模拟实时文本输入(比如从语音识别或用户输入获得)
        async def simulate_real_time_input():
            """模拟实时文本输入流"""
            for i, query in enumerate(customer_queries):
                logger.info(f"💬 客服回复 {i+1}: {query}")
                yield query
                # 模拟思考时间 - 在真实场景中, 这可能是语音识别的延迟
                await asyncio.sleep(1.5)

        player = StreamingAudioPlayer()
        total_responses = 0
        synthesis_start_time = time.time()

        try:
            # 关键: 使用 synthesize_stream 进行流式合成, 获得最低延迟
            async for result in client.synthesize_stream(simulate_real_time_input(), config):
                # 立即播放收到的音频块, 不等待完整音频
                await player.play_audio_chunk(
                    result.audio_data,
                    result.text_index,
                    result.chunk_index
                )

                # 记录延迟指标
                if result.chunk_index == 1:  # 第一个音频块
                    latency = player.get_latency_ms(synthesis_start_time)
                    logger.info(f"⚡ 首包延迟: {latency:.1f}ms (文本 {result.text_index})")
                    total_responses += 1

        except Exception as e:
            logger.error(f"合成过程中出现错误: {e}")

        # 显示性能指标
        total_time = time.time() - synthesis_start_time
        logger.info("📊 对话完成统计:")
        logger.info(f"   总回复数: {total_responses}")
        logger.info(f"   总耗时: {total_time:.2f}秒")
        logger.info(f"   音频块数: {player.total_audio_chunks}")
        if total_responses > 0:
            logger.info(f"   平均每回复时间: {total_time/total_responses:.2f}秒")
        else:
            logger.info("   平均每回复时间: N/A (没有成功的合成)")

        logger.info("\n🔑 实时客服场景最佳实践:")
        logger.info("1. 使用 synthesize_stream() 而不是 collect_audio() 获得最低延迟")
        logger.info("2. 收到第一个音频块就立即开始播放, 无需等待完整音频")
        logger.info("3. 配置合适的语速(speed)和音色来匹配客服场景")
        logger.info("4. 监控首包延迟(TTFB)确保用户体验")
        logger.info("5. 可以与ASR集成实现全双工实时对话")


async def conversation_simulation():
    """Conversation simulation example"""

    async with cosyvoice.connect_client() as client:
        logger.info("=== Conversation simulation example ===")

        # Create multiple speakers (simulate different speakers)
        speakers = {
            "alice": {
                "config": cosyvoice.SynthesisConfig(
                    speaker_id="alice_speaker",
                    mode=cosyvoice.SynthesisMode.ZERO_SHOT,
                    speed=1.0
                ),
                "name": "Alice"
            },
            "bob": {
                "config": cosyvoice.SynthesisConfig(
                    speaker_id="bob_speaker",
                    mode=cosyvoice.SynthesisMode.ZERO_SHOT,
                    speed=0.9
                ),
                "name": "Bob"
            }
        }

        # Conversation content
        conversation = [
            ("alice", "Hello Bob, nice weather today!"),
            ("bob", "Yes Alice, it's really nice weather. What are your plans today?"),
            ("alice", "I'm planning to go for a walk in the park, want to come along?"),
            ("bob", "Sure, I'd like to go out too. What time shall we meet?"),
            ("alice", "How about 2 PM? Meet at the park entrance."),
            ("bob", "Sounds good, see you at 2 PM!")
        ]

        # Generate separate audio files for each speaker
        conversation_audio = {}

        for speaker_id, (speaker_key, text) in enumerate(conversation):
            speaker_name = speakers[speaker_key]["name"]
            config = speakers[speaker_key]["config"]

            logger.info(f"{speaker_name}: {text}")

            # Synthesize speech
            audio_data = await client.collect_audio(text, config)

            # Save audio file
            output_file = Path("output") / "conversation" / f"{speaker_id:02d}_{speaker_key}.wav"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "wb") as f:
                f.write(audio_data)

            conversation_audio[speaker_id] = {
                "speaker": speaker_name,
                "text": text,
                "audio_file": output_file,
                "audio_size": len(audio_data)
            }

            logger.info(f"Audio saved to: {output_file} ({len(audio_data)} bytes)")

            # Simulate conversation interval
            await asyncio.sleep(1.0)

        logger.info("Conversation synthesis completed")

        # Generate conversation summary
        total_audio_size = sum(item["audio_size"] for item in conversation_audio.values())
        logger.info("Conversation stats:")
        logger.info(f"  Total rounds: {len(conversation)}")
        logger.info(f"  Total audio size: {total_audio_size} bytes")
        logger.info(f"  Average per round: {total_audio_size / len(conversation):.0f} bytes")


async def stress_test_synthesis():
    """Stress test example"""

    async with cosyvoice.connect_client() as client:
        logger.info("=== Stress test ===")

        config = cosyvoice.SynthesisConfig(
            speaker_id="demo_speaker_001",
            mode=cosyvoice.SynthesisMode.ZERO_SHOT
        )

        # Generate a lot of text
        test_texts = [
            f"This is stress test text number {i+1}. We are testing the system's concurrent processing capabilities and stability."
            for i in range(20)
        ]

        start_time = time.time()
        total_audio_size = 0
        successful_syntheses = 0

        # Concurrent synthesis test
        async def synthesize_single_text(text_id: int, text: str):
            nonlocal total_audio_size, successful_syntheses

            try:
                logger.info(f"Starting synthesis of text {text_id}: {text[:30]}...")

                audio_data = await client.collect_audio(text, config)

                total_audio_size += len(audio_data)
                successful_syntheses += 1

                logger.info(f"Text {text_id} synthesis completed: {len(audio_data)} bytes")

                # Save audio
                output_file = Path("output") / "stress_test" / f"text_{text_id:02d}.wav"
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, "wb") as f:
                    f.write(audio_data)

                return len(audio_data)

            except Exception as e:
                logger.error(f"Text {text_id} synthesis failed: {e}")
                return 0

        # Limit concurrency
        semaphore = asyncio.Semaphore(3)  # Maximum 3 concurrent syntheses

        async def limited_synthesis(text_id: int, text: str):
            async with semaphore:
                return await synthesize_single_text(text_id, text)

        # Execute concurrent synthesis
        tasks = [limited_synthesis(i, text) for i, text in enumerate(test_texts)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Display results
        total_time = time.time() - start_time

        logger.info("Stress test completed")
        logger.info("Test results:")
        logger.info(f"  Total texts: {len(test_texts)}")
        logger.info(f"  Successful syntheses: {successful_syntheses}")
        logger.info(f"  Failures: {len(test_texts) - successful_syntheses}")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Average per text: {total_time / len(test_texts):.2f}s")
        logger.info(f"  Total audio size: {total_audio_size} bytes")
        logger.info(f"  Throughput: {total_audio_size / total_time:.0f} bytes/s")


if __name__ == "__main__":
    # Run example (choose one)

    # Real-time synthesis with event handling
    # asyncio.run(realtime_synthesis_with_events())

    # Customer service simulation (recommended for real-time scenarios)
    asyncio.run(customer_service_simulation())

    # Conversation simulation
    # asyncio.run(conversation_simulation())

    # Stress test
    # asyncio.run(stress_test_synthesis())

    print("Real-time streaming synthesis example completed!")
