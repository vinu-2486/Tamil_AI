"""Unit tests for the Tamil pronunciation assessment pipeline."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np

from app.models.schemas import PhonemeError, PronunciationResult, ProsodyResult
from app.services.feedback_generator import generate_feedback
from app.services.phonemes import (
    compute_phoneme_similarity,
    detect_tamil_confusions,
    text_to_ipa,
)
from app.services.pronunciation_scorer import (
    compute_content_accuracy,
    compute_fluency_score,
    compute_overall_score,
)
from app.services.alignment import WordSegment


def test_text_to_ipa() -> None:
    """Assert Tamil text produces a non-empty IPA string.

    Args:
        None.

    Returns:
        None.
    """
    assert text_to_ipa("வணக்கம்")


def test_phoneme_similarity_identical() -> None:
    """Assert identical IPA strings have perfect similarity.

    Args:
        None.

    Returns:
        None.
    """
    assert compute_phoneme_similarity("ʋaɳakkam", "ʋaɳakkam") == 1.0


def test_tamil_confusion_detection() -> None:
    """Assert a known Tamil confusion is detected.

    Args:
        None.

    Returns:
        None.
    """
    detected = detect_tamil_confusions("ɻ", "l", "ழ")
    assert "ழ→ல" in detected


def test_prosody_scorer_silent_audio(tmp_path) -> None:
    """Assert silent audio returns a zero prosody score.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None.
    """
    soundfile = __import__("pytest").importorskip("soundfile")
    from app.services.prosody_scorer import extract_prosody_features

    audio_path = tmp_path / "silent.wav"
    soundfile.write(audio_path, np.zeros(16000, dtype=np.float32), 16000)
    result = extract_prosody_features(str(audio_path))
    assert result.prosody_score == 0


def test_content_accuracy_perfect() -> None:
    """Assert perfect text match has full content accuracy.

    Args:
        None.

    Returns:
        None.
    """
    assert compute_content_accuracy("வணக்கம்", "வணக்கம்") == 100.0


def test_fluency_score_range() -> None:
    """Assert fluency score is always in score bounds.

    Args:
        None.

    Returns:
        None.
    """
    segments = [
        WordSegment("வணக்கம்", 0.0, 0.5, 1.0),
        WordSegment("தமிழ்", 0.8, 1.2, 1.0),
    ]
    score = compute_fluency_score(segments, 1.5)
    assert 0.0 <= score <= 100.0


def test_overall_score_formula() -> None:
    """Assert the weighted score formula is exact.

    Args:
        None.

    Returns:
        None.
    """
    pronunciation = 80.0
    content = 90.0
    prosody = 70.0
    overall = compute_overall_score(pronunciation, content, prosody)
    assert overall == (0.50 * pronunciation) + (0.30 * content) + (0.20 * prosody)


@patch("app.services.feedback_generator._call_openai", return_value="Good effort. Keep practicing ழ sounds.")
def test_generate_feedback_result(mock_call) -> None:
    """Assert feedback generation returns the weighted overall score.

    Args:
        mock_call: Patched OpenAI call.

    Returns:
        None.
    """
    error = PhonemeError(
        word="தமிழ்",
        expected_ipa="tamiɻ",
        actual_ipa="tamil",
        error_type="substitution",
        tamil_confusion="ழ→ல",
        confidence=0.8,
    )
    pronunciation = PronunciationResult(
        content_accuracy=90.0,
        pronunciation_accuracy=80.0,
        fluency_score=75.0,
        phoneme_errors=[error],
        wer=0.1,
        cer=0.05,
    )
    prosody = ProsodyResult(
        pitch_mean=200.0,
        pitch_std=10.0,
        pitch_range=50.0,
        speaking_rate_syllables_per_sec=4.0,
        pause_count=0,
        pause_duration_total=0.0,
        energy_mean=0.1,
        prosody_score=70.0,
    )
    result = generate_feedback(pronunciation, prosody, "தமிழ்", "தமிழ்")
    assert result.overall_score == 81.0
    assert mock_call.called
