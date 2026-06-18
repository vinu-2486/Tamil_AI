"""Transcript-to-audio alignment helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WordSegment:
    """Aligned word timing segment."""

    word: str
    start_time: float
    end_time: float
    confidence: float


def _detect_device() -> str:
    """Detect the preferred torch device.

    Returns:
        ``cuda`` when available, otherwise ``cpu``.
    """
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@lru_cache(maxsize=1)
def _load_align_model(language_code: str = "ta") -> tuple[object, object]:
    """Load the WhisperX alignment model once.

    Args:
        language_code: Language code for the aligner.

    Returns:
        Alignment model and metadata.

    Raises:
        RuntimeError: If WhisperX cannot load the aligner.
    """
    try:
        import whisperx

        device = _detect_device()
        return whisperx.load_align_model(language_code=language_code, device=device)
    except Exception as exc:
        logger.warning("Unable to load WhisperX alignment model: %s", exc)
        raise RuntimeError("Unable to load alignment model") from exc


def _audio_duration(audio_path: str) -> float:
    """Return audio duration in seconds.

    Args:
        audio_path: Path to an audio file.

    Returns:
        Duration in seconds.
    """
    import librosa

    return float(librosa.get_duration(path=audio_path))


def _fallback_alignment(audio_path: str, transcript: str) -> list[dict[str, float | str]]:
    """Create equal-duration word segments.

    Args:
        audio_path: Path to an audio file.
        transcript: Transcript text.

    Returns:
        List of word timing dictionaries.
    """
    words = [word for word in transcript.split() if word]
    if not words:
        return []
    duration = max(_audio_duration(audio_path), 0.01)
    step = duration / len(words)
    return [
        {
            "word": word,
            "start": round(index * step, 3),
            "end": round((index + 1) * step, 3),
            "score": 0.0,
        }
        for index, word in enumerate(words)
    ]


def align_transcript(
    audio_path: str,
    transcript: str,
    language: str = "ta",
) -> list[dict[str, float | str]]:
    """Align transcript words to audio timestamps.

    Args:
        audio_path: Path to the audio file.
        transcript: STT or reference transcript.
        language: Alignment language code.

    Returns:
        List of dictionaries with word, start, end, and score.
    """
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not transcript.strip():
        return []
    try:
        import whisperx

        model, metadata = _load_align_model(language)
        audio = whisperx.load_audio(audio_path)
        duration = _audio_duration(audio_path)
        result = {"segments": [{"start": 0.0, "end": duration, "text": transcript}]}
        aligned = whisperx.align(result["segments"], model, metadata, audio, _detect_device())
        words = aligned.get("word_segments", [])
        normalized = []
        for word in words:
            normalized.append(
                {
                    "word": str(word.get("word", "")).strip(),
                    "start": float(word.get("start", 0.0)),
                    "end": float(word.get("end", 0.0)),
                    "score": float(word.get("score", 0.0)),
                }
            )
        return [word for word in normalized if word["word"]]
    except Exception as exc:
        logger.warning("WhisperX alignment failed; using fallback alignment: %s", exc)
        return _fallback_alignment(audio_path, transcript)


def get_word_segments(alignment_result: list[dict[str, float | str]]) -> list[WordSegment]:
    """Convert alignment dictionaries to WordSegment dataclasses.

    Args:
        alignment_result: Alignment dictionaries.

    Returns:
        WordSegment list.
    """
    return [
        WordSegment(
            word=str(item["word"]),
            start_time=float(item["start"]),
            end_time=float(item["end"]),
            confidence=float(item.get("score", 0.0)),
        )
        for item in alignment_result
    ]
