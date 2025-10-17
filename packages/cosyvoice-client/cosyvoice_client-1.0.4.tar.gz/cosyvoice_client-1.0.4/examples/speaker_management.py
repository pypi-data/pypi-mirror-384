"""Speaker management example

Demonstrates how to use CosyVoice Python SDK for speaker management.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

import cosyvoice

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Force reconfiguration of logging
)
logger = logging.getLogger(__name__)

# Also set the cosyvoice logger to DEBUG level
cosyvoice_logger = logging.getLogger('cosyvoice')
cosyvoice_logger.setLevel(logging.DEBUG)

# Try to load .env file for development
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, using system environment variables only")

# Debug: Print environment variable status
logger.debug(f"COSYVOICE_BASE_URL in env: {'Yes' if os.environ.get('COSYVOICE_BASE_URL') else 'No'}")
logger.debug(f"COSYVOICE_API_KEY in env: {'Yes' if os.environ.get('COSYVOICE_API_KEY') else 'No'}")


def get_config():
    """Get configuration from environment variables"""
    server_url = os.environ.get('COSYVOICE_BASE_URL')
    api_key = os.environ.get('COSYVOICE_API_KEY')

    if not server_url:
        logger.error("COSYVOICE_BASE_URL environment variable is required")
        logger.error("Please set it with: export COSYVOICE_BASE_URL='https://your-server-url'")
        logger.error("Or create a .envrc file with the configuration")
        sys.exit(1)

    if not api_key:
        logger.error("COSYVOICE_API_KEY environment variable is required")
        logger.error("Please set it with: export COSYVOICE_API_KEY='your-api-key'")
        logger.error("Or create a .envrc file with the configuration")
        sys.exit(1)

    logger.info(f"Using server URL: {server_url}")
    logger.info(f"API Key configured: {'Yes' if api_key else 'No'}")
    return server_url, api_key


async def speaker_management_without_websocket():
    """Speaker management example without WebSocket connection"""

    print("=== Starting speaker management example ===")
    logger.info("Initializing speaker management example...")

    # Get configuration from environment variables
    server_url, api_key = get_config()

    # Create speaker manager directly (no WebSocket needed)
    from cosyvoice.speaker.manager import SpeakerManager

    print(f"Initializing speaker manager with server: {server_url}")
    logger.info(f"Connecting to server: {server_url}")

    try:
        async with SpeakerManager(server_url=server_url, api_key=api_key) as speaker_mgr:
            logger.info("Speaker manager initialized successfully (no WebSocket connection needed)")
            print("Speaker manager initialized successfully!")

            # 1. Create speaker
            logger.info("=== Create speaker ===")
            print("Creating speaker...")

            speaker_id = f"test_speaker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            prompt_text = "希望你以后能够做的比我还好呦。"
            prompt_audio_path = "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"

            logger.info(f"Speaker ID: {speaker_id}")
            logger.info(f"Prompt text: {prompt_text}")
            logger.info(f"Prompt audio: {prompt_audio_path}")

            try:
                speaker_info = await speaker_mgr.create(
                    prompt_text=prompt_text,
                    zero_shot_spk_id=speaker_id,
                    prompt_audio_path=prompt_audio_path
                )

                logger.info("Speaker created successfully!")
                logger.info(f"  Speaker ID: {speaker_info.zero_shot_spk_id}")
                logger.info(f"  Reference text: {speaker_info.prompt_text}")
                logger.info(f"  Audio URL: {speaker_info.audio_url}")
                print("✓ Speaker created successfully!")

            except cosyvoice.SpeakerError as e:
                logger.error(f"Speaker creation failed: {e}")
                print(f"✗ Speaker creation failed: {e}")
                return

            # 2. Get speaker information
            logger.info("=== Get speaker information ===")
            print("Getting speaker information...")

            speaker_info = await speaker_mgr.get_info(speaker_id)
            logger.info("Speaker information:")
            logger.info(f"  ID: {speaker_info.zero_shot_spk_id}")
            logger.info(f"  Reference text: {speaker_info.prompt_text}")
            logger.info(f"  Created at: {speaker_info.created_at}")
            logger.info(f"  Audio URL: {speaker_info.audio_url}")
            print("✓ Speaker information retrieved!")

            # 3. Check if speaker exists
            logger.info("=== Check speaker existence ===")
            print("Checking speaker existence...")

            exists = await speaker_mgr.exists(speaker_id)
            logger.info(f"Speaker {speaker_id} exists: {exists}")
            print(f"✓ Speaker {speaker_id} exists: {exists}")

            exists = await speaker_mgr.exists("nonexistent_speaker")
            logger.info(f"Nonexistent speaker exists: {exists}")
            print(f"✓ Nonexistent speaker exists: {exists}")

            # 4. Update speaker
            logger.info("=== Update speaker ===")
            print("Updating speaker...")

            new_prompt_text = "这是更新后的参考文本。"
            try:
                updated_speaker = await speaker_mgr.update(
                    zero_shot_spk_id=speaker_id,
                    prompt_text=new_prompt_text
                )

                logger.info(f"Speaker updated successfully, new reference text: {updated_speaker.prompt_text}")
                print("✓ Speaker updated successfully!")

            except cosyvoice.SpeakerError as e:
                logger.warning(f"Speaker update failed: {e}")
                print(f"⚠ Speaker update failed: {e}")

            logger.info("=== Speaker management example completed ===")
            print("✓ Speaker management example completed!")

    except Exception as e:
        logger.error(f"Speaker manager initialization failed: {e}")
        print(f"✗ Speaker manager initialization failed: {e}")
        raise


async def batch_speaker_creation_example():
    """批量创建音色示例"""
    print("=== Starting batch speaker creation example ===")

    # Get configuration from environment variables
    server_url, api_key = get_config()

    from cosyvoice.speaker.manager import SpeakerManager

    print(f"Initializing speaker manager with server: {server_url}")

    async with SpeakerManager(server_url=server_url, api_key=api_key) as speaker_mgr:
        logger.info("=== 批量创建音色 ===")
        print("Starting batch speaker creation...")

        # 定义多个音色
        speakers_to_create = [
            {
                "zero_shot_spk_id": "speaker_female_001",
                "prompt_text": "你好, 我是女声音色。",
                "prompt_audio_path": "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
            },
            {
                "zero_shot_spk_id": "speaker_male_001",
                "prompt_text": "你好, 我是男声音色。",
                "prompt_audio_path": "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
            },
            {
                "zero_shot_spk_id": "speaker_child_001",
                "prompt_text": "你好, 我是儿童音色。",
                "prompt_audio_path": "https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
            }
        ]

        # 并发创建音色
        async def create_speaker(speaker_config):
            try:
                logger.info(f"开始创建音色: {speaker_config['zero_shot_spk_id']}")

                speaker_info = await speaker_mgr.create(
                    prompt_text=speaker_config['prompt_text'],
                    zero_shot_spk_id=speaker_config['zero_shot_spk_id'],
                    prompt_audio_path=speaker_config['prompt_audio_path']
                )

                logger.info(f"音色创建成功: {speaker_info.zero_shot_spk_id}")
                return speaker_info

            except Exception as e:
                logger.error(f"创建音色 {speaker_config['zero_shot_spk_id']} 失败: {e}")
                return None

        # 并发执行创建任务
        tasks = [create_speaker(config) for config in speakers_to_create]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计结果
        successful_speakers = [r for r in results if r is not None and not isinstance(r, Exception)]
        logger.info(f"成功创建 {len(successful_speakers)} 个音色")


async def speaker_monitoring_example():
    """音色状态监控示例"""
    print("=== Starting speaker monitoring example ===")

    # Get configuration from environment variables
    server_url, api_key = get_config()

    from cosyvoice.speaker.manager import SpeakerManager

    print(f"Initializing speaker manager with server: {server_url}")

    async with SpeakerManager(server_url=server_url, api_key=api_key) as speaker_mgr:
        logger.info("=== 音色状态监控 ===")
        print("Starting speaker monitoring...")
        # 创建一个音色并监控其状态变化
        speaker_id = f"monitor_speaker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 不等待创建完成, 手动监控状态
        await speaker_mgr.create(
            prompt_text="这是状态监控测试音色。",
            zero_shot_spk_id=speaker_id,
            prompt_audio_path="https://edu-public-assets.edu-aliyun.com/zero_shot_prompt.wav"
        )

        logger.info(f"音色 {speaker_id} 创建请求已提交, 开始监控状态...")

        # 手动监控状态变化
        max_checks = 30  # 最多检查 30 次

        for i in range(max_checks):
            try:
                speaker_info = await speaker_mgr.get_info(speaker_id)

                logger.info(f"检查 {i+1}: 状态 = {speaker_info}")

                # Since SpeakerInfo doesn't have status/is_ready fields like before,
                # we'll just check if we can get the info successfully
                logger.info("音色创建完成!")
                break

            except cosyvoice.SpeakerError as e:
                logger.error(f"获取音色状态失败: {e}")
                break
        else:
            logger.warning("监控超时, 音色可能仍在创建中")

        # 清理: 删除测试音色
        try:
            await speaker_mgr.delete(speaker_id)
            logger.info(f"测试音色 {speaker_id} 已清理")
        except Exception as e:
            logger.warning(f"清理测试音色失败: {e}")


if __name__ == "__main__":
    # 运行示例(选择一个)

    # 完整音色管理示例 (需要 WebSocket 连接)
    # asyncio.run(speaker_management_example())

    # 音色管理示例 (无需 WebSocket 连接)
    asyncio.run(speaker_management_without_websocket())

    # 批量创建音色示例
    # asyncio.run(batch_speaker_creation_example())

    # 音色状态监控示例
    # asyncio.run(speaker_monitoring_example())

    # 服务器连接测试
    # asyncio.run(test_server_connection())

    print("音色管理示例执行完成!")
