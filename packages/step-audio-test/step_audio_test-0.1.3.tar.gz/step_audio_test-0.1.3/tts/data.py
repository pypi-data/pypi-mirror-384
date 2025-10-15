import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional


class TTSClientEventType(Enum):
    """Event types sent from client to server"""
    CREATE = "tts.create"
    TEXT_DELTA = "tts.text.delta"
    TEXT_DONE = "tts.text.done"
    FLUSH = "tts.text.flush"


class TTSServerEventType(Enum):
    """Event types sent from server to client"""
    CONNECTION_DONE = "tts.connection.done"
    RESPONSE_CREATED = "tts.response.created"
    RESPONSE_AUDIO_DELTA = "tts.response.audio.delta"
    RESPONSE_AUDIO_DONE = "tts.response.audio.done"
    RESPONSE_ERROR = "tts.response.error"
    TEXT_FLUSHED = "tts.text.flushed"
    RESPONSE_SENTENCE_START = "tts.response.sentence.start"
    RESPONSE_SENTENCE_END = "tts.response.sentence.end"
    RESPONSE_AUDIO_PAUSED = "tts.response.audio.paused"


class TTSInternalEventType(Enum):
    """Client internal event types (only used for cases that cannot be mapped to protocol events)"""
    # Connection status events
    CONNECTED = "internal.connected"
    DISCONNECTED = "internal.disconnected"

    # Error handling events
    ERROR = "internal.error"
    PARSE_ERROR = "internal.parse_error"
    MESSAGE_ERROR = "internal.message_error"
    AUDIO_DECODE_ERROR = "internal.audio_decode_error"
    UNKNOWN_EVENT = "internal.unknown_event"


class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OPUS = "opus"
    MP3_STREAM = "mp3_stream"


class AudioStatus(Enum):
    """Audio generation status"""
    UNFINISHED = "unfinished"
    FINISHED = "finished"


@dataclass
class AudioChunk:
    """Audio data chunk"""
    data: bytes
    session_id: str
    status: str = AudioStatus.UNFINISHED.value
    duration: Optional[float] = None
    is_final: bool = False


@dataclass
class ServerEventData:
    """Base class for server event data"""
    session_id: str
    event_id: str
    event_type: str


@dataclass
class ConnectionDoneData(ServerEventData):
    """Connection done event data"""
    pass


@dataclass
class ResponseCreatedData(ServerEventData):
    """Response created event data"""
    pass


@dataclass
class AudioDeltaData(ServerEventData):
    """Audio delta data"""
    status: str
    audio: str  # Base64 encoded
    duration: Optional[float] = None


@dataclass
class AudioDoneData(ServerEventData):
    """Audio done data"""
    audio: str  # Base64 encoded


@dataclass
class ErrorData(ServerEventData):
    """Error data"""
    code: str
    message: str
    details: Dict[str, Any]


@dataclass
class FlushedData(ServerEventData):
    """Flush completed data"""
    pass


@dataclass
class SentenceEventData(ServerEventData):
    """Sentence event data"""
    text: str
    request_id: str
    timestamp: int


@dataclass
class AudioPausedData(ServerEventData):
    """Audio paused event data"""
    pass


class ClientEvent:
    """Client event"""

    def __init__(self, event_type: TTSClientEventType, data: Any = None):
        self.event_id = str(uuid.uuid4())
        self.type = event_type.value
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "event_id": self.event_id,
            "type": self.type
        }
        if self.data is not None:
            if hasattr(self.data, '__dict__'):
                result["data"] = asdict(self.data)
            else:
                result["data"] = self.data
        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class ServerEvent:
    """Server event"""

    def __init__(self, event_data: Dict[str, Any]):
        self.event_id = event_data.get("event_id", "")
        self.type = event_data.get("type", "")
        self.raw_data = event_data
        self.data = event_data.get("data", {})

        # Parse specific data structure
        self.parsed_data = self._parse_data()

    def _parse_data(self) -> ServerEventData:
        """Parse event data"""
        base_data = {
            "session_id": self.data.get("session_id", ""),
            "event_id": self.event_id,
            "event_type": self.type
        }

        if self.type == TTSServerEventType.CONNECTION_DONE.value:
            return ConnectionDoneData(**base_data)

        elif self.type == TTSServerEventType.RESPONSE_CREATED.value:
            return ResponseCreatedData(**base_data)

        elif self.type == TTSServerEventType.RESPONSE_AUDIO_DELTA.value:
            return AudioDeltaData(
                **base_data,
                status=self.data.get("status", AudioStatus.UNFINISHED.value),
                audio=self.data.get("audio", ""),
                duration=self.data.get("duration")
            )

        elif self.type == TTSServerEventType.RESPONSE_AUDIO_DONE.value:
            return AudioDoneData(
                **base_data,
                audio=self.data.get("audio", "")
            )

        elif self.type == TTSServerEventType.RESPONSE_ERROR.value:
            return ErrorData(
                **base_data,
                code=self.data.get("code", ""),
                message=self.data.get("message", ""),
                details=self.data.get("details", {})
            )

        elif self.type == TTSServerEventType.TEXT_FLUSHED.value:
            return FlushedData(**base_data)

        elif self.type == TTSServerEventType.RESPONSE_SENTENCE_START.value:
            return SentenceEventData(
                **base_data,
                text=self.data.get("text", ""),
                request_id=self.data.get("request_id", ""),
                timestamp=self.data.get("timestamp", 0)
            )

        elif self.type == TTSServerEventType.RESPONSE_SENTENCE_END.value:
            return SentenceEventData(
                **base_data,
                text=self.data.get("text", ""),
                request_id=self.data.get("request_id", ""),
                timestamp=self.data.get("timestamp", 0)
            )

        elif self.type == TTSServerEventType.RESPONSE_AUDIO_PAUSED.value:
            return AudioPausedData(**base_data)

        else:
            return ServerEventData(**base_data)