from typing import Dict, Any


class StepFunTTSError(Exception):
    """TTS SDK base exception"""
    pass


class ConnectionError(StepFunTTSError):
    """WebSocket connection error"""
    pass


class AuthenticationError(StepFunTTSError):
    """Authentication error"""
    pass


class TTSConfigError(StepFunTTSError):
    """TTS configuration error"""
    pass


class TTSServerError(StepFunTTSError):
    """TTS server error"""

    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"TTSServerError [{code}]: {message}")