"""Prosody feature extraction and scoring."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from app.models.schemas import ProsodyResult

logger = logging.getLogger(__name__)


def _clip_score(value: float) -> float:
    """Clip a score to 0.0 through 100.0.

    Args:
        value: Raw score value.

    Returns:
        Clipped score.
    """
    return max(0.0, min(100.0, float(value)))


def _silent_result() -> ProsodyResult:
    """Build an empty prosody result for silent audio.

    Returns:
        ProsodyResult with zero-valued features.
    """
    return ProsodyResult(
        pitch_mean=0.0,
        pitch_std=0.0,
        pitch_range=0.0,
        speaking_rate_syllables_per_sec=0.0,
        pause_count=0,
        pause_duration_total=0.0,
        energy_mean=0.0,
        prosody_score=0.0,
    )


def _pitch_features(audio_path: str) -> tuple[float, float, float]:
    """Extract pitch summary features with Parselmouth.

    Args:
        audio_path: Path to an audio file.

    Returns:
        Mean, standard deviation, and range of voiced F0 values.
    """
    try:
        import parselmouth

        sound = parselmouth.Sound(str(audio_path))
        pitch = sound.to_pitch()
        frequencies = pitch.selected_array["frequency"]
        voiced = frequencies[frequencies > 0]
        if voiced.size == 0:
            return 0.0, 0.0, 0.0
        return float(np.mean(voiced)), float(np.std(voiced)), float(np.ptp(voiced))
    except Exception as exc:
        logger.warning("Pitch extraction failed: %s", exc)
        return 0.0, 0.0, 0.0


def _pause_features(rms: np.ndarray, frame_duration: float, threshold: float = 0.01) -> tuple[int, float]:
    """Compute pause count and total duration from RMS frames.

    Args:
        rms: RMS energy per frame.
        frame_duration: Frame duration in seconds.
        threshold: Silence threshold.

    Returns:
        Pause count and total pause duration.
    """
    silent = rms < threshold
    pause_count = 0
    pause_frames = 0
    in_pause = False
    for is_silent in silent:
        if is_silent:
            pause_frames += 1
            if not in_pause:
                pause_count += 1
                in_pause = True
        else:
            in_pause = False
    return pause_count, float(pause_frames * frame_duration)


def extract_prosody_features(audio_path: str) -> ProsodyResult:
    """Extract pitch, speaking rate, pauses, energy, and prosody score.

    Args:
        audio_path: Path to an audio file.

    Returns:
        ProsodyResult with clipped score.

    Raises:
        FileNotFoundError: If the audio file does not exist.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    import librosa

    audio, sample_rate = librosa.load(path, sr=16000, mono=True)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0 or np.allclose(audio, 0.0):
        logger.warning("Silent audio detected; returning zero prosody score")
        return _silent_result()

    rms_matrix = librosa.feature.rms(y=audio)
    rms = np.asarray(rms_matrix[0], dtype=np.float32)
    energy_mean = float(np.mean(rms))
    duration = max(float(librosa.get_duration(y=audio, sr=sample_rate)), 0.001)
    peaks = librosa.util.peak_pick(rms, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.005, wait=3)
    speaking_rate = float(len(peaks) / duration)
    frame_duration = 512 / float(sample_rate)
    pause_count, pause_duration = _pause_features(rms, frame_duration)
    pitch_mean, pitch_std, pitch_range = _pitch_features(str(path))

    pitch_score = 100.0 - min(abs(pitch_mean - 200.0) / 2.0, 50.0)
    rate_score = 100.0 - min(abs(speaking_rate - 4.0) * 10.0, 100.0)
    pause_penalty = min(pause_count * 5.0, 30.0)
    prosody_score = _clip_score((0.4 * pitch_score + 0.4 * rate_score) - pause_penalty)

    return ProsodyResult(
        pitch_mean=pitch_mean,
        pitch_std=pitch_std,
        pitch_range=pitch_range,
        speaking_rate_syllables_per_sec=speaking_rate,
        pause_count=pause_count,
        pause_duration_total=pause_duration,
        energy_mean=energy_mean,
        prosody_score=prosody_score,
    )
