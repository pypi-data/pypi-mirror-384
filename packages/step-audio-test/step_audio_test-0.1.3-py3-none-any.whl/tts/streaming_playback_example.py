import asyncio
import json
import os
import platform
import subprocess
import tempfile
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, List


class BrowserAudioPlayer:
    """浏览器音频播放器 - 零依赖方案"""

    def __init__(self, port: int = 8888, auto_open_browser: bool = True):
        self.port = port
        self.auto_open_browser = auto_open_browser
        self.temp_dir = tempfile.mkdtemp(prefix="tts_audio_")
        self.audio_files: List[str] = []
        self.is_playing = False
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.chunk_counter = 0

        print(f"🌐 临时目录: {self.temp_dir}")

    def start(self):
        """启动 HTTP 服务器"""
        if self.is_playing:
            return

        self.is_playing = True

        # 启动 HTTP 服务器
        self._start_http_server()

        # 创建播放页面
        self._create_player_page()

        # 自动打开浏览器
        if self.auto_open_browser:
            player_url = f"http://localhost:{self.port}/player.html"
            print(f"🔊 浏览器播放器已启动: {player_url}")
            self._open_browser_with_retry(player_url)
        else:
            print(f"🔊 浏览器播放器已启动，请手动访问: http://localhost:{self.port}/player.html")

    def _open_browser_with_retry(self, url: str, max_retries: int = 3):
        """多种方式尝试打开浏览器"""

        def try_open_browser():
            for attempt in range(max_retries):
                try:
                    print(f"🌐 尝试打开浏览器 (第{attempt + 1}次)...")

                    # 方法1: 使用webbrowser模块
                    if self._try_webbrowser_open(url):
                        print("✅ 浏览器已成功打开 (webbrowser)")
                        return

                    # 方法2: 根据操作系统使用系统命令
                    if self._try_system_open(url):
                        print("✅ 浏览器已成功打开 (系统命令)")
                        return

                    print(f"⚠️ 第{attempt + 1}次尝试失败，等待重试...")
                    time.sleep(2)

                except Exception as e:
                    print(f"❌ 第{attempt + 1}次打开浏览器失败: {e}")
                    time.sleep(2)

            print(f"❌ 尝试{max_retries}次后仍无法自动打开浏览器")
            print(f"💡 请手动在浏览器中访问: {url}")

        # 延迟执行，确保服务器完全启动
        threading.Timer(1.5, try_open_browser).start()

    def _try_webbrowser_open(self, url: str) -> bool:
        """尝试使用webbrowser模块打开"""
        try:
            # 尝试获取默认浏览器
            browser = webbrowser.get()
            browser.open(url)
            return True
        except Exception as e:
            print(f"webbrowser模块失败: {e}")
            return False

    def _try_system_open(self, url: str) -> bool:
        """尝试使用系统命令打开"""
        try:
            system = platform.system()

            if system == "Windows":
                # Windows
                subprocess.run(['start', url], shell=True, check=True)
            elif system == "Darwin":
                # macOS
                subprocess.run(['open', url], check=True)
            elif system == "Linux":
                # Linux - 尝试多个命令
                commands = ['xdg-open', 'gnome-open', 'kde-open', 'firefox', 'google-chrome', 'chromium-browser']
                for cmd in commands:
                    try:
                        subprocess.run([cmd, url], check=True, timeout=5)
                        return True
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                return False
            else:
                print(f"不支持的操作系统: {system}")
                return False

            return True
        except Exception as e:
            print(f"系统命令失败: {e}")
            return False

    def set_auto_open_browser(self, enabled: bool):
        """设置是否自动打开浏览器"""
        self.auto_open_browser = enabled

    def get_player_url(self) -> str:
        """获取播放器URL"""
        return f"http://localhost:{self.port}/player.html"

    def stop(self):
        """停止播放器"""
        if not self.is_playing:
            return

        self.is_playing = False

        # 停止服务器
        if self.server:
            self.server.shutdown()
            self.server = None

        if self.server_thread:
            self.server_thread.join(timeout=2.0)

        # 清理临时文件
        self._cleanup_temp_files()

        print("🔇 浏览器播放器已停止")

    def add_audio_data(self, audio_data: bytes):
        """添加音频数据 - 保存为文件并通知浏览器"""
        if not self.is_playing:
            return

        try:
            self.chunk_counter += 1
            filename = f"chunk_{self.chunk_counter:04d}.wav"
            filepath = os.path.join(self.temp_dir, filename)

            # 保存音频文件
            with open(filepath, 'wb') as f:
                f.write(audio_data)

            self.audio_files.append(filename)

            # 更新播放列表
            self._update_playlist()

            print(f"🎵 保存音频块: {filename} ({len(audio_data)} 字节)")

        except Exception as e:
            print(f"⚠️ 保存音频文件出错: {e}")

    def _start_http_server(self):
        """启动 HTTP 服务器"""
        try:
            # 切换到临时目录
            os.chdir(self.temp_dir)

            class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
                def log_message(self, format, *args):
                    # 禁用日志输出
                    pass

                def end_headers(self):
                    # 添加 CORS 头部
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', '*')
                    super().end_headers()

            self.server = HTTPServer(("", self.port), CustomHTTPRequestHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            # 等待服务器启动
            time.sleep(0.5)
            print(f"🌐 HTTP服务器已启动在端口 {self.port}")

        except Exception as e:
            print(f"❌ 启动 HTTP 服务器失败: {e}")

    def _create_player_page(self):
        """创建播放页面"""
        html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StepFun TTS 浏览器播放器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .player {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .status {
            background: #e8f5e8;
            border: 1px solid #4CAF50;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
            color: #2E7D32;
        }
        .audio-item {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 5px;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }
        button:disabled {
            background: #cccccc;
            cursor: not-allowed;
        }
        .log {
            background: #f0f0f0;
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 5px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .success-message {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 StepFun TTS 浏览器播放器</h1>

        <div class="success-message">
            ✅ 浏览器已成功自动打开！
        </div>

        <div class="status" id="status">
            等待音频数据...
        </div>

        <div class="controls">
            <button onclick="startAutoPlay()">🔊 开启自动播放</button>
            <button onclick="stopAutoPlay()">⏹️ 停止自动播放</button>
            <button onclick="clearPlaylist()">🗑️ 清空播放列表</button>
        </div>

        <div class="player">
            <h3>📱 当前播放</h3>
            <audio id="currentPlayer" controls style="width: 100%;">
                您的浏览器不支持音频播放
            </audio>
        </div>

        <div class="player">
            <h3>📋 播放列表 (<span id="playlistCount">0</span> 个文件)</h3>
            <div id="playlist"></div>
        </div>

        <div class="player">
            <h3>📜 播放日志</h3>
            <div id="log" class="log"></div>
        </div>
    </div>

    <script>
        let autoPlay = false;
        let currentIndex = 0;
        let playlist = [];
        let checkInterval;

        function log(message) {
            const logDiv = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logDiv.innerHTML += `[${time}] ${message}<br>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }

        function updateStatus(message) {
            document.getElementById('status').textContent = message;
            log(message);
        }

        function startAutoPlay() {
            autoPlay = true;
            updateStatus('🔊 自动播放已开启');

            // 每秒检查新文件
            checkInterval = setInterval(checkForNewFiles, 1000);
            checkForNewFiles(); // 立即检查一次
        }

        function stopAutoPlay() {
            autoPlay = false;
            if (checkInterval) {
                clearInterval(checkInterval);
            }
            updateStatus('⏹️ 自动播放已停止');
        }

        function clearPlaylist() {
            playlist = [];
            currentIndex = 0;
            document.getElementById('playlist').innerHTML = '';
            document.getElementById('playlistCount').textContent = '0';
            updateStatus('🗑️ 播放列表已清空');
        }

        async function checkForNewFiles() {
            try {
                // 检查是否有新的音频文件
                const response = await fetch('playlist.json');
                if (response.ok) {
                    const newPlaylist = await response.json();

                    // 比较播放列表
                    if (newPlaylist.length > playlist.length) {
                        const newFiles = newPlaylist.slice(playlist.length);
                        playlist = newPlaylist;

                        // 更新显示
                        updatePlaylistDisplay();

                        // 自动播放新文件
                        if (autoPlay) {
                            for (const filename of newFiles) {
                                await playAudioFile(filename);
                            }
                        }
                    }
                }
            } catch (error) {
                // 忽略错误，文件可能还没创建
            }
        }

        function updatePlaylistDisplay() {
            const playlistDiv = document.getElementById('playlist');
            const countSpan = document.getElementById('playlistCount');

            countSpan.textContent = playlist.length;

            playlistDiv.innerHTML = '';
            playlist.forEach((filename, index) => {
                const div = document.createElement('div');
                div.className = 'audio-item';
                div.innerHTML = `
                    <strong>${filename}</strong>
                    <button onclick="playAudioFile('${filename}')" style="float: right;">▶️ 播放</button>
                `;
                playlistDiv.appendChild(div);
            });
        }

        function playAudioFile(filename) {
            return new Promise((resolve) => {
                const player = document.getElementById('currentPlayer');
                player.src = filename;

                updateStatus(`🎵 正在播放: ${filename}`);

                player.onended = () => {
                    updateStatus(`✅ 播放完成: ${filename}`);
                    resolve();
                };

                player.onerror = () => {
                    updateStatus(`❌ 播放出错: ${filename}`);
                    resolve();
                };

                player.play().catch(error => {
                    updateStatus(`❌ 播放失败: ${filename} - ${error.message}`);
                    resolve();
                });
            });
        }

        // 页面加载完成后启动
        window.onload = function() {
            log('✅ 浏览器播放器已成功加载');
            updateStatus('🚀 播放器就绪，点击"开启自动播放"开始');
        };
    </script>
</body>
</html>'''

        player_path = os.path.join(self.temp_dir, "player.html")
        with open(player_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _update_playlist(self):
        """更新播放列表 JSON 文件"""
        try:
            playlist_path = os.path.join(self.temp_dir, "playlist.json")
            with open(playlist_path, 'w', encoding='utf-8') as f:
                json.dump(self.audio_files, f)
        except Exception as e:
            print(f"⚠️ 更新播放列表出错: {e}")

    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


async def browser_streaming_example():
    """浏览器流式播放示例"""

    # 导入必要的 TTS 模块（需要确保已安装）
    try:
        from tts.client import StepFunTTS
        from tts.config import TTSConfig
        from tts.data import AudioChunk, AudioFormat, TTSServerEventType
        from tts.err import TTSServerError
    except ImportError:
        print("❌ 请确保已安装 StepFun TTS 相关模块")
        return

    # 创建 TTS 客户端
    tts = StepFunTTS(
        api_key="your api key",
    )

    # 音频数据收集
    audio_chunks = []

    # 创建浏览器播放器，启用自动打开浏览器
    player = BrowserAudioPlayer(port=8888, auto_open_browser=True)

    def on_connection_done(data):
        print(f"✅ 连接完成，Session ID: {data.session_id}")

    def on_response_created(data):
        print("📝 TTS 响应已创建")
        # 启动浏览器播放器
        player.start()

    def on_audio_delta(chunk: AudioChunk):
        """处理音频增量数据 - 在浏览器中播放"""
        audio_chunks.append(chunk.data)
        status_icon = "🔄" if chunk.status == "unfinished" else "✅"
        print(f"{status_icon} 收到音频块: {len(chunk.data)} 字节, 状态: {chunk.status}")

        # 在浏览器中播放音频块
        player.add_audio_data(chunk.data)

    def on_audio_done(chunk: AudioChunk):
        """处理音频完成数据"""
        audio_chunks.append(chunk.data)
        print(f"🎵 收到完整音频: {len(chunk.data)} 字节")

        # 播放最后的音频块
        player.add_audio_data(chunk.data)

    def on_server_error(error: TTSServerError):
        print(f"❌ 服务器错误: {error}")
        player.stop()

    # 注册事件处理器
    tts.on(TTSServerEventType.CONNECTION_DONE, on_connection_done)
    tts.on(TTSServerEventType.RESPONSE_CREATED, on_response_created)
    tts.on(TTSServerEventType.RESPONSE_AUDIO_DELTA, on_audio_delta)
    tts.on(TTSServerEventType.RESPONSE_AUDIO_DONE, on_audio_done)
    tts.on(TTSServerEventType.RESPONSE_ERROR, on_server_error)

    try:
        print("🌐 开始浏览器流式播放示例")
        print("=" * 40)

        # 连接
        await tts.connect(model="step-tts-mini")

        # 创建会话
        config = TTSConfig(
            voice_id="cixingnansheng",
            response_format=AudioFormat.WAV.value,
            volume_ratio=1.2,
            speed_ratio=1.0,
            sample_rate=24000
        )
        await tts.create_session(config)

        # 发送文本
        text = "欢迎使用改进的浏览器播放器！这是一个具有自动打开浏览器功能的零依赖音频播放解决方案。每个音频片段都会在浏览器中自动播放。"
        await tts.send_text(text)
        await tts.finish_text()

        # 监听响应
        await asyncio.wait_for(tts.listen(), timeout=30)

        print("⏳ 等待播放完成...")
        print("💡 请在浏览器中点击'开启自动播放'按钮")
        await asyncio.sleep(10)  # 给用户时间操作浏览器

        # 保存完整音频文件
        if audio_chunks:
            audio_data = b''.join(audio_chunks)
            output_path = os.path.join(player.temp_dir, "complete_audio.wav")
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print(f"💾 完整音频已保存: {output_path} ({len(audio_data)} 字节)")

    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
    finally:
        print("🔄 播放器将在 10 秒后自动关闭...")
        await asyncio.sleep(10)
        player.stop()
        await tts.disconnect()
        print("🎉 浏览器流式播放示例完成")


if __name__ == "__main__":
    print("StepFun TTS 浏览器播放示例 (改进版)")
    print("=" * 40)
    asyncio.run(browser_streaming_example())
