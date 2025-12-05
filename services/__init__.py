# при добавлении новых сервисов - добавлять в __all__
"""Декларация сервисов."""
from .screenshot_service import ScreenshotService
from .speech_service import SpeechService
from .audio_capture_service import AudioCaptureService

__all__ = ['ScreenshotService', 'SpeechService', 'AudioCaptureService']
