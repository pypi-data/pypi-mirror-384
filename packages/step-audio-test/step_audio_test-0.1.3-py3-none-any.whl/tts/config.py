import uuid
from dataclasses import dataclass
from typing import Optional, Dict, List

from tts.data import AudioFormat
from tts.err import TTSConfigError

@dataclass
class PronunciationMap():
    tone: List[str]

@dataclass
class TTSConfig:
    """TTS configuration parameters"""
    voice_id: str
    response_format: str = AudioFormat.WAV.value
    volume_ratio: float = 1.0
    speed_ratio: float = 1.0
    sample_rate: int = 24000
    session_id: str = ""
    voice_label: Optional[Dict[str, str]] = None
    mode: Optional[str] = None
    pronunciation_map: PronunciationMap = None

    def __post_init__(self):
        """Validate configuration parameters"""
        if not (0.1 <= self.volume_ratio <= 2.0):
            raise TTSConfigError("volume_ratio must be between 0.1-2.0")
        if not (0.5 <= self.speed_ratio <= 2.0):
            raise TTSConfigError("speed_ratio must be between 0.5-2.0")
        if self.response_format not in [f.value for f in AudioFormat]:
            raise TTSConfigError(f"Unsupported audio format: {self.response_format}")