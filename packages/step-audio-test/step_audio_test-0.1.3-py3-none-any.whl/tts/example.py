import asyncio
import logging

from tts.client import StepFunTTS, TTSStreamer
from tts.config import TTSConfig
from tts.data import (
    AudioChunk, AudioFormat,
    TTSServerEventType, TTSClientEventType, TTSInternalEventType
)
from tts.err import TTSServerError


async def basic_example():
    """基本使用示例 - 使用协议定义的事件类型"""
    # 创建 TTS 客户端
    tts = StepFunTTS(api_key="your-api-key-here")

    # 音频数据收集
    audio_chunks = []

    def on_connection_done(data):
        print(f"✅ 连接完成，Session ID: {data.session_id}")

    def on_response_created(data):
        print("📝 TTS 响应已创建")

    def on_audio_delta(chunk: AudioChunk):
        """处理音频增量数据 (对应服务端的 RESPONSE_AUDIO_DELTA)"""
        audio_chunks.append(chunk.data)
        status_icon = "🔄" if chunk.status == "unfinished" else "✅"
        print(f"{status_icon} 收到音频块: {len(chunk.data)} 字节, 状态: {chunk.status}")

    def on_audio_done(chunk: AudioChunk):
        """处理音频完成数据 (对应服务端的 RESPONSE_AUDIO_DONE)"""
        audio_chunks.append(chunk.data)
        print(f"🎵 收到完整音频: {len(chunk.data)} 字节")

    def on_server_error(error: TTSServerError):
        print(f"❌ 服务器错误: {error}")

    # 注册事件处理器 - 使用协议定义的事件类型
    tts.on(TTSServerEventType.CONNECTION_DONE, on_connection_done)
    tts.on(TTSServerEventType.RESPONSE_CREATED, on_response_created)
    tts.on(TTSServerEventType.RESPONSE_AUDIO_DELTA, on_audio_delta)
    tts.on(TTSServerEventType.RESPONSE_AUDIO_DONE, on_audio_done)
    tts.on(TTSServerEventType.RESPONSE_ERROR, on_server_error)

    try:
        # 连接
        await tts.connect(model="step-tts-1")

        # 创建会话
        config = TTSConfig(
            voice_id="voice_001",
            response_format=AudioFormat.WAV.value,
            volume_ratio=1.2,
            speed_ratio=1.0
        )
        await tts.create_session(config)

        # 发送文本
        await tts.send_text("Hello, this is a test of StepFun TTS API with real server events.")
        await tts.finish_text()

        # 监听响应
        await asyncio.wait_for(tts.listen(), timeout=30)

        # 合并音频数据
        if audio_chunks:
            audio_data = b''.join(audio_chunks)
            with open("output.wav", "wb") as f:
                f.write(audio_data)
            print(f"💾 音频已保存到 output.wav ({len(audio_data)} 字节)")

    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
    finally:
        await tts.disconnect()


async def comprehensive_event_handling_example():
    """完整事件处理示例 - 展示所有事件类型"""
    tts = StepFunTTS(api_key="your-api-key-here")

    # 事件统计
    event_counts = {}

    def track_event(event_name):
        def handler(data):
            event_counts[event_name] = event_counts.get(event_name, 0) + 1
            print(f"📊 事件 [{event_name}] 触发 (第{event_counts[event_name]}次)")
            if data and hasattr(data, '__dict__'):
                print(f"   数据: {data.__class__.__name__}")
            elif data:
                print(f"   数据: {type(data).__name__}")

        return handler

    # 注册所有协议事件处理器
    # 服务端事件
    server_events = [
        TTSServerEventType.CONNECTION_DONE,
        TTSServerEventType.RESPONSE_CREATED,
        TTSServerEventType.RESPONSE_AUDIO_DELTA,
        TTSServerEventType.RESPONSE_AUDIO_DONE,
        TTSServerEventType.RESPONSE_ERROR,
        TTSServerEventType.TEXT_FLUSHED,
    ]

    # 客户端事件（监听自己发送的事件）
    client_events = [
        TTSClientEventType.CREATE,
        TTSClientEventType.TEXT_DELTA,
        TTSClientEventType.TEXT_DONE,
        TTSClientEventType.FLUSH,
    ]

    # 内部事件
    internal_events = [
        TTSInternalEventType.CONNECTED,
        TTSInternalEventType.DISCONNECTED,
        TTSInternalEventType.ERROR,
        TTSInternalEventType.PARSE_ERROR,
        TTSInternalEventType.MESSAGE_ERROR,
        TTSInternalEventType.AUDIO_DECODE_ERROR,
        TTSInternalEventType.UNKNOWN_EVENT,
    ]

    for event_type in server_events + client_events + internal_events:
        tts.on(event_type, track_event(event_type.value))

    try:
        print("🚀 开始完整事件处理示例")
        print("=" * 50)

        # 连接
        await tts.connect(model="step-tts-1")

        # 创建会话
        config = TTSConfig(
            voice_id="voice_001",
            response_format=AudioFormat.WAV.value,
            volume_ratio=1.0,
            speed_ratio=1.0
        )
        await tts.create_session(config)

        # 分段发送文本
        text_segments = [
            "这是第一段文本。",
            "这是第二段文本。",
            "这是最后一段文本。"
        ]

        for segment in text_segments:
            await tts.send_text(segment)
            await asyncio.sleep(0.1)  # 小延迟以便观察事件

        await tts.finish_text()

        # 可选：刷新管道
        await tts.flush()

        # 监听响应
        await asyncio.wait_for(tts.listen(), timeout=30)

        print("\n📈 事件统计:")
        print("-" * 30)
        for event_name, count in sorted(event_counts.items()):
            print(f"  {event_name}: {count} 次")

    except Exception as e:
        print(f"❌ 完整示例运行出错: {e}")
    finally:
        await tts.disconnect()


async def streaming_example():
    """流式处理示例"""
    streamer = TTSStreamer(api_key="your-api-key-here")

    try:
        chunks = await streamer.synthesize(
            text="这是一个基于真实服务端事件的流式 TTS 演示。服务端会发送增量音频数据和完成事件。",
            model="step-tts-1",
            voice_id="voice_001",
            audio_format=AudioFormat.WAV,
            volume_ratio=1.0,
            speed_ratio=1.2
        )

        print(f"✅ 合成完成! 收到 {len(chunks)} 个音频块")

        # 显示每个音频块的详情
        total_duration = 0
        for i, chunk in enumerate(chunks, 1):
            duration_str = f", 时长: {chunk.duration}s" if chunk.duration else ""
            final_str = " (最终块)" if chunk.is_final else ""
            print(f"  📦 块 {i}: {len(chunk.data)} 字节, 状态: {chunk.status}{duration_str}{final_str}")
            if chunk.duration:
                total_duration += chunk.duration

        if total_duration > 0:
            print(f"🕐 总时长: {total_duration:.2f} 秒")

        # 获取完整音频数据
        audio_data = streamer.get_audio_data()

        # 保存到文件
        with open("streaming_output.wav", "wb") as f:
            f.write(audio_data)

        print(f"💾 音频已保存: {len(audio_data)} 字节")

    except Exception as e:
        print(f"❌ 流式处理出错: {e}")


async def error_handling_example():
    """错误处理示例"""
    tts = StepFunTTS(api_key="invalid-key-for-testing")  # 故意使用无效密钥

    error_events = []

    def on_internal_error(error):
        error_events.append(("internal_error", error))
        print(f"🚨 内部错误: {error}")

    def on_server_error(error):
        error_events.append(("server_error", error))
        print(f"🚨 服务器错误: {error}")

    def on_parse_error(error):
        error_events.append(("parse_error", error))
        print(f"🚨 解析错误: {error}")

    def on_audio_decode_error(error):
        error_events.append(("audio_decode_error", error))
        print(f"🚨 音频解码错误: {error}")

    # 注册错误事件处理器 - 使用内部事件类型
    tts.on(TTSInternalEventType.ERROR, on_internal_error)
    tts.on(TTSServerEventType.RESPONSE_ERROR, on_server_error)
    tts.on(TTSInternalEventType.PARSE_ERROR, on_parse_error)
    tts.on(TTSInternalEventType.AUDIO_DECODE_ERROR, on_audio_decode_error)

    try:
        print("🧪 错误处理示例 (使用无效API密钥)")
        print("=" * 40)

        # 尝试连接 (应该会失败)
        await tts.connect(model="step-tts-1")

    except Exception as e:
        print(f"✅ 预期的连接错误: {e}")

    finally:
        print(f"\n📊 捕获到 {len(error_events)} 个错误事件")
        for error_type, error_data in error_events:
            print(f"  - {error_type}: {error_data}")
        await tts.disconnect()


async def protocol_alignment_example():
    """协议对齐示例 - 展示事件与协议的映射关系"""
    tts = StepFunTTS(api_key="your-api-key-here")

    print("🔄 协议事件对齐示例")
    print("=" * 40)
    print("客户端发送的事件 -> 服务端接收")
    print("服务端发送的事件 -> 客户端接收")
    print("内部事件 -> 仅客户端内部使用")
    print()

    def on_client_create(data):
        print(f"📤 客户端发送: {TTSClientEventType.CREATE.value}")

    def on_client_text_delta(data):
        print(f"📤 客户端发送: {TTSClientEventType.TEXT_DELTA.value} - {data}")

    def on_client_text_done(data):
        print(f"📤 客户端发送: {TTSClientEventType.TEXT_DONE.value}")

    def on_server_connection_done(data):
        print(f"📥 服务端响应: {TTSServerEventType.CONNECTION_DONE.value}")

    def on_server_response_created(data):
        print(f"📥 服务端响应: {TTSServerEventType.RESPONSE_CREATED.value}")

    def on_server_audio_delta(chunk):
        print(f"📥 服务端响应: {TTSServerEventType.RESPONSE_AUDIO_DELTA.value} - {len(chunk.data)} 字节")

    def on_internal_connected(data):
        print(f"🔧 内部事件: {TTSInternalEventType.CONNECTED.value}")

    # 注册所有事件类型的处理器
    tts.on(TTSClientEventType.CREATE, on_client_create)
    tts.on(TTSClientEventType.TEXT_DELTA, on_client_text_delta)
    tts.on(TTSClientEventType.TEXT_DONE, on_client_text_done)
    tts.on(TTSServerEventType.CONNECTION_DONE, on_server_connection_done)
    tts.on(TTSServerEventType.RESPONSE_CREATED, on_server_response_created)
    tts.on(TTSServerEventType.RESPONSE_AUDIO_DELTA, on_server_audio_delta)
    tts.on(TTSInternalEventType.CONNECTED, on_internal_connected)

    try:
        await tts.connect(model="step-tts-1")

        config = TTSConfig(voice_id="voice_001", response_format=AudioFormat.WAV.value)
        await tts.create_session(config)

        await tts.send_text("示例文本")
        await tts.finish_text()

        # 简短监听以查看事件
        await asyncio.wait_for(tts.listen(), timeout=10)

    except Exception as e:
        print(f"⚠️ 示例过程中的错误: {e}")
    finally:
        await tts.disconnect()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("StepFun TTS SDK 示例 (协议对齐版本)")
    print("=" * 50)
    print("选择运行模式:")
    print("1. 基本事件驱动示例")
    print("2. 完整事件处理示例")
    print("3. 流式处理示例")
    print("4. 错误处理示例")
    print("5. 协议对齐示例")

    choice = input("请选择 (1-5): ").strip()

    if choice == "1":
        print("运行基本示例...")
        asyncio.run(basic_example())
    elif choice == "2":
        print("运行完整事件处理示例...")
        asyncio.run(comprehensive_event_handling_example())
    elif choice == "3":
        print("运行流式处理示例...")
        asyncio.run(streaming_example())
    elif choice == "4":
        print("运行错误处理示例...")
        asyncio.run(error_handling_example())
    elif choice == "5":
        print("运行协议对齐示例...")
        asyncio.run(protocol_alignment_example())
    else:
        print("❌ 无效选择")
        print("默认运行基本示例...")
        asyncio.run(basic_example())