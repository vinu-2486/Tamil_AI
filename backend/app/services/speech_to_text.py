"""Speech-to-text service for Tamil audio."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_model_lock = threading.Lock()
_model = None


def _get_model() -> object:
    """Load the faster-whisper model once, on first use.

    Returns:
        Loaded WhisperModel instance.

    Raises:
        RuntimeError: If model loading fails.
    """
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        try:
            from faster_whisper import WhisperModel

            _model = WhisperModel("small", device="cpu", compute_type="int8")
            return _model
        except Exception as exc:
            logger.exception("Unable to load STT model")
            raise RuntimeError("Unable to load STT model") from exc


def transcribe(audio_path: str) -> str:
    """Transcribe Tamil speech from an audio file.

    Args:
        audio_path: Path to an audio file.

    Returns:
        Transcript text exactly as produced by faster-whisper segments.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        RuntimeError: If transcription fails.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    try:
        segments, _ = _get_model().transcribe(str(path), language="ta")
        return " ".join(segment.text for segment in segments)
    except Exception as exc:
        logger.exception("Tamil transcription failed")
        raise RuntimeError("Tamil transcription failed") from exc
