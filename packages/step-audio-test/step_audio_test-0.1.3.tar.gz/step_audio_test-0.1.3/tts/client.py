"""
StepFun TTS Streaming Audio Generation SDK
WebSocket implementation based on actual server-side events
"""

import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional, Callable, List, Union

import websockets

from tts.config import TTSConfig
from tts.data import (
    ServerEvent, TTSServerEventType, AudioDoneData, AudioChunk, AudioStatus,
    ClientEvent, TTSClientEventType, AudioDeltaData, ErrorData, AudioFormat,
    TTSInternalEventType, SentenceEventData, AudioPausedData
)
from tts.err import TTSServerError


class StepFunTTS:
    """StepFun TTS streaming audio generation client"""

    def __init__(
            self,
            api_key: str,
            base_url: str = "wss://api.stepfun.com",
            timeout: float = 30.0,
            logger: Optional[logging.Logger] = None
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self._websocket: Optional[Any] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._is_connected = False  # Only True after receiving CONNECTION_DONE
        self._websocket_connected = False  # WebSocket connection status
        self._is_listening = False
        self._session_id: Optional[str] = None
        self._synthesis_complete = False
        self._connection_done_event = asyncio.Event()  # Used to wait for CONNECTION_DONE

    def _get_connection_url(self, model: str) -> str:
        """Build WebSocket connection URL"""
        return f"{self.base_url}/v1/realtime/audio?model={model}"

    def _get_headers(self) -> Dict[str, str]:
        """Get connection headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "StepFun-TTS-Python-SDK/1.0.0"
        }

    def on(self, event_type: Union[str, TTSClientEventType, TTSServerEventType, TTSInternalEventType],
           handler: Callable):
        """Register event handler"""
        if hasattr(event_type, 'value'):
            event_type = event_type.value

        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        self.logger.debug(f"Register event handler: {event_type}")

    def off(self, event_type: Union[str, TTSClientEventType, TTSServerEventType, TTSInternalEventType],
            handler: Callable):
        """Remove event handler"""
        if hasattr(event_type, 'value'):
            event_type = event_type.value

        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                self.logger.debug(f"Remove event handler: {event_type}")
            except ValueError:
                pass

    def _emit_event(self, event_type: Union[TTSClientEventType, TTSServerEventType, TTSInternalEventType],
                    data: Any = None):
        """Trigger event"""
        event_name = event_type.value
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                self.logger.error(f"Event handler error {event_name}: {e}")

    async def connect(self, model: str) -> None:
        """Connect to TTS service"""
        if self._is_connected:
            await self.disconnect()

        # Reset connection state
        self._is_connected = False
        self._websocket_connected = False
        self._connection_done_event.clear()
        self._session_id = None

        url = self._get_connection_url(model)
        headers = self._get_headers()

        try:
            self.logger.info(f"Connecting to TTS service: {url}")
            self._websocket = await websockets.connect(
                url,
                additional_headers=headers,
                open_timeout=self.timeout,
                close_timeout=self.timeout
            )
            self._websocket_connected = True
            self.logger.info("WebSocket connected successfully, waiting for CONNECTION_DONE event")

            # Start message listening task
            listen_task = asyncio.create_task(self._listen_for_connection_done())

            try:
                # Wait for CONNECTION_DONE event with timeout
                await asyncio.wait_for(self._connection_done_event.wait(), timeout=self.timeout)
                self.logger.info("TTS service connection fully established")
            except asyncio.TimeoutError:
                listen_task.cancel()
                raise ConnectionError("Timeout waiting for CONNECTION_DONE event")
            finally:
                if not listen_task.done():
                    listen_task.cancel()

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            await self.disconnect()
            raise ConnectionError(f"Unable to connect to TTS service: {e}")

    async def _listen_for_connection_done(self):
        """Listen for CONNECTION_DONE event"""
        try:
            while self._websocket_connected and not self._connection_done_event.is_set():
                try:
                    message = await asyncio.wait_for(
                        self._websocket.recv(),
                        timeout=10.0
                    )
                    await self._handle_message(message)
                except asyncio.TimeoutError:
                    continue  # Continue waiting
                except websockets.exceptions.ConnectionClosed:
                    break
        except Exception as e:
            self.logger.error(f"Error while listening for CONNECTION_DONE: {e}")

    async def disconnect(self) -> None:
        """Disconnect"""
        self._is_listening = False
        self._synthesis_complete = False
        self._websocket_connected = False

        if self._websocket is not None:
            try:
                await self._websocket.close()
                self.logger.info("TTS service connection disconnected")
                self._emit_event(TTSInternalEventType.DISCONNECTED)
            except Exception as e:
                self.logger.error(f"Error during disconnection: {e}")
            finally:
                self._websocket = None
                self._is_connected = False
                self._session_id = None
                self._connection_done_event.clear()

    async def _send_event(self, event: ClientEvent) -> None:
        """Send event to server"""
        if not self._is_connected or self._websocket is None:
            raise ConnectionError("Not connected to TTS service or connection not fully established")

        try:
            message = event.to_json()
            await self._websocket.send(message)
            self.logger.debug(f"Sending event: {event.type}")
        except Exception as e:
            self.logger.error(f"Failed to send event: {e}")
            raise ConnectionError(f"Failed to send event: {e}")

    async def create_session(self, config: TTSConfig) -> None:
        """Create TTS session"""
        if not self._is_connected:
            raise ConnectionError("Please connect to TTS service first and wait for connection completion")

        config.session_id = self._session_id
        event = ClientEvent(TTSClientEventType.CREATE, config)
        await self._send_event(event)
        self.logger.info("TTS session creation request sent")
        self._emit_event(TTSClientEventType.CREATE, config)

    async def send_text(self, text: str) -> None:
        """Send text segment"""
        if not self._is_connected:
            raise ConnectionError("Please connect to TTS service first and wait for connection completion")

        event = ClientEvent(TTSClientEventType.TEXT_DELTA, {"text": text, "session_id": self._session_id})
        await self._send_event(event)
        self.logger.debug(f"Sending text: {text[:50]}...")
        self._emit_event(TTSClientEventType.TEXT_DELTA, text)

    async def finish_text(self) -> None:
        """Mark text input as complete"""
        if not self._is_connected:
            raise ConnectionError("Please connect to TTS service first and wait for connection completion")

        event = ClientEvent(TTSClientEventType.TEXT_DONE, {"session_id": self._session_id})
        await self._send_event(event)
        self.logger.debug("Text input completed")
        self._emit_event(TTSClientEventType.TEXT_DONE)

    async def flush(self) -> None:
        """Flush TTS pipeline"""
        if not self._is_connected:
            raise ConnectionError("Please connect to TTS service first and wait for connection completion")

        event = ClientEvent(TTSClientEventType.FLUSH, {"session_id": self._session_id})
        await self._send_event(event)
        self.logger.debug("Flushing TTS pipeline")
        self._emit_event(TTSClientEventType.FLUSH)

    async def listen(self) -> None:
        """Listen for server responses"""
        if not self._is_connected or self._websocket is None:
            raise ConnectionError("Not connected to TTS service or connection not fully established")

        self._is_listening = True
        self._synthesis_complete = False
        self.logger.info("Starting to listen for TTS responses")

        try:
            while self._is_listening and self._websocket and not self._synthesis_complete:
                try:
                    # Wait for message
                    message = await asyncio.wait_for(
                        self._websocket.recv(),
                        timeout=self.timeout
                    )

                    await self._handle_message(message)

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    await self._websocket.ping()
                    continue
                except websockets.exceptions.ConnectionClosed:
                    self.logger.info("WebSocket connection closed")
                    break

        except Exception as e:
            self.logger.error(f"Error during listening: {e}")
            self._emit_event(TTSInternalEventType.ERROR, str(e))
            raise ConnectionError(f"Listening failed: {e}")
        finally:
            self._is_listening = False

    async def _handle_message(self, message: str) -> None:
        """Handle server message"""
        try:
            if isinstance(message, bytes):
                # Binary message - might be audio data, but according to protocol should be JSON
                self.logger.warning("Received binary message, but expected JSON format")
                return

            # Parse JSON message
            data = json.loads(message)
            server_event = ServerEvent(data)

            self.logger.debug(f"Received server event: {server_event.type}")

            # Handle different types of server events
            await self._process_server_event(server_event)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON message: {e}")
            self._emit_event(TTSInternalEventType.PARSE_ERROR, str(e))
        except Exception as e:
            self.logger.error(f"Error while processing message: {e}")
            self._emit_event(TTSInternalEventType.MESSAGE_ERROR, str(e))

    async def _process_server_event(self, event: ServerEvent) -> None:
        """Process server event"""
        event_type = event.type

        if event_type == TTSServerEventType.CONNECTION_DONE.value:
            self._session_id = event.parsed_data.session_id
            self._is_connected = True  # Only set to True here
            self._connection_done_event.set()  # Set event to wake up waiting connection process
            self.logger.info(f"Connection established, Session ID: {self._session_id}")
            self._emit_event(TTSServerEventType.CONNECTION_DONE, event.parsed_data)

        elif event_type == TTSServerEventType.RESPONSE_CREATED.value:
            self.logger.info("TTS response created")
            self._emit_event(TTSServerEventType.RESPONSE_CREATED, event.parsed_data)

        elif event_type == TTSServerEventType.RESPONSE_AUDIO_DELTA.value:
            # Handle audio delta data
            audio_data = event.parsed_data
            if isinstance(audio_data, AudioDeltaData) and audio_data.audio:
                try:
                    # Decode Base64 audio data
                    audio_bytes = base64.b64decode(audio_data.audio)
                    chunk = AudioChunk(
                        data=audio_bytes,
                        session_id=audio_data.session_id,
                        status=audio_data.status,
                        duration=audio_data.duration,
                        is_final=(audio_data.status == AudioStatus.FINISHED.value)
                    )

                    self.logger.debug(f"Received audio chunk: {len(audio_bytes)} bytes, status: {audio_data.status}")
                    self._emit_event(TTSServerEventType.RESPONSE_AUDIO_DELTA, chunk)

                    # If status is finished, mark synthesis as complete
                    if audio_data.status == AudioStatus.FINISHED.value:
                        self._synthesis_complete = True

                except Exception as e:
                    self.logger.error(f"Failed to decode audio data: {e}")
                    self._emit_event(TTSInternalEventType.AUDIO_DECODE_ERROR, str(e))

        elif event_type == TTSServerEventType.RESPONSE_AUDIO_DONE.value:
            # Handle audio completion event
            audio_data = event.parsed_data
            if isinstance(audio_data, AudioDoneData) and audio_data.audio:
                try:
                    # Decode complete audio data
                    audio_bytes = base64.b64decode(audio_data.audio)
                    chunk = AudioChunk(
                        data=audio_bytes,
                        session_id=audio_data.session_id,
                        status=AudioStatus.FINISHED.value,
                        is_final=True
                    )

                    self.logger.info(f"Received complete audio: {len(audio_bytes)} bytes")
                    self._emit_event(TTSServerEventType.RESPONSE_AUDIO_DONE, chunk)
                    self._synthesis_complete = True

                except Exception as e:
                    self.logger.error(f"Failed to decode complete audio data: {e}")
                    self._emit_event(TTSInternalEventType.AUDIO_DECODE_ERROR, str(e))

        elif event_type == TTSServerEventType.RESPONSE_ERROR.value:
            # Handle error event
            error_data = event.parsed_data
            if isinstance(error_data, ErrorData):
                error = TTSServerError(
                    code=error_data.code,
                    message=error_data.message,
                    details=error_data.details
                )
                self.logger.error(f"Server error: {error}")
                self._emit_event(TTSServerEventType.RESPONSE_ERROR, error)
                self._synthesis_complete = True  # Also terminate listening on error

        elif event_type == TTSServerEventType.TEXT_FLUSHED.value:
            self.logger.info("Text flushing completed")
            self._emit_event(TTSServerEventType.TEXT_FLUSHED, event.parsed_data)

        elif event_type == TTSServerEventType.RESPONSE_SENTENCE_START.value:
            self.logger.debug("Sentence started")
            self._emit_event(TTSServerEventType.RESPONSE_SENTENCE_START, event.parsed_data)

        elif event_type == TTSServerEventType.RESPONSE_SENTENCE_END.value:
            self.logger.debug("Sentence ended")
            self._emit_event(TTSServerEventType.RESPONSE_SENTENCE_END, event.parsed_data)

        elif event_type == TTSServerEventType.RESPONSE_AUDIO_PAUSED.value:
            self.logger.info("Audio paused")
            self._emit_event(TTSServerEventType.RESPONSE_AUDIO_PAUSED, event.parsed_data)

        else:
            # Unknown event type
            self.logger.warning(f"Unknown server event type: {event_type}")
            self._emit_event(TTSInternalEventType.UNKNOWN_EVENT, event)

    @property
    def is_connected(self) -> bool:
        """Check if connected (received CONNECTION_DONE)"""
        return self._is_connected

    @property
    def websocket_connected(self) -> bool:
        """Check WebSocket connection status"""
        return self._websocket_connected

    @property
    def is_listening(self) -> bool:
        """Check if listening"""
        return self._is_listening

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self._session_id

    @property
    def synthesis_complete(self) -> bool:
        """Check if synthesis is complete"""
        return self._synthesis_complete


# ============================================================================
# Convenience wrapper class
# ============================================================================

class TTSStreamer:
    """TTS streaming processing convenience class"""

    def __init__(self, api_key: str, base_url: str = "wss://api.stepfun.com"):
        self.tts = StepFunTTS(api_key, base_url)
        self.audio_chunks: List[AudioChunk] = []
        self.synthesis_complete = False
        self.connection_done = False
        self.response_created = False

        # Register event handlers - using protocol-defined event types
        self.tts.on(TTSServerEventType.CONNECTION_DONE, self._on_connection_done)
        self.tts.on(TTSServerEventType.RESPONSE_CREATED, self._on_response_created)
        self.tts.on(TTSServerEventType.RESPONSE_AUDIO_DELTA, self._on_audio_chunk)
        self.tts.on(TTSServerEventType.RESPONSE_AUDIO_DONE, self._on_audio_complete)
        self.tts.on(TTSServerEventType.RESPONSE_ERROR, self._on_error)

    def _on_connection_done(self, data):
        """Handle connection completion"""
        self.connection_done = True

    def _on_response_created(self, data):
        """Handle response creation"""
        self.response_created = True

    def _on_audio_chunk(self, chunk: AudioChunk):
        """Handle audio chunk"""
        self.audio_chunks.append(chunk)
        # Check if complete
        if chunk.is_final:
            self.synthesis_complete = True

    def _on_audio_complete(self, chunk: AudioChunk):
        """Handle audio completion"""
        self.audio_chunks.append(chunk)
        self.synthesis_complete = True

    def _on_error(self, error: TTSServerError):
        """Handle error"""
        raise error

    async def synthesize(
            self,
            text: str,
            model: str,
            voice_id: str,
            audio_format: Union[str, AudioFormat] = AudioFormat.WAV,
            volume_ratio: float = 1.0,
            speed_ratio: float = 1.0,
            sample_rate: int = 24000,
            voice_label: Optional[Dict[str, str]] = None
    ) -> List[AudioChunk]:
        """Synthesize text to audio in one go"""

        # Reset state
        self.audio_chunks.clear()
        self.synthesis_complete = False
        self.connection_done = False
        self.response_created = False

        # Configuration
        if isinstance(audio_format, AudioFormat):
            audio_format = audio_format.value

        config = TTSConfig(
            voice_id=voice_id,
            response_format=audio_format,
            volume_ratio=volume_ratio,
            speed_ratio=speed_ratio,
            sample_rate=sample_rate,
            voice_label=voice_label,
        )

        try:
            # Connect and setup (will wait for CONNECTION_DONE event)
            await self.tts.connect(model)

            # Wait for connection completion confirmation
            if not self.connection_done:
                timeout = 10.0
                start_time = asyncio.get_event_loop().time()
                while not self.connection_done:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        raise TimeoutError("Timeout waiting for connection completion")
                    await asyncio.sleep(0.1)

            # Create session
            await self.tts.create_session(config)

            # Send text
            await self.tts.send_text(text)
            await self.tts.finish_text()

            # Listen for responses
            listen_task = asyncio.create_task(self.tts.listen())

            # Wait for synthesis completion
            timeout = 60.0  # 60 second timeout
            start_time = asyncio.get_event_loop().time()

            while not self.synthesis_complete:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("TTS synthesis timeout")
                await asyncio.sleep(0.1)

            listen_task.cancel()
            return self.audio_chunks.copy()

        finally:
            await self.tts.disconnect()

    def get_audio_data(self) -> bytes:
        """Get merged audio data"""
        return b''.join(chunk.data for chunk in self.audio_chunks)
