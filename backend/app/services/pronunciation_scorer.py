"""Pronunciation accuracy scoring with text, phoneme, and acoustic signals."""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Sequence

import numpy as np

from app.models.schemas import PhonemeError, PronunciationResult
from app.services.acoustic_scorer import extract_segment_embeddings
from app.services.alignment import WordSegment, align_transcript, get_word_segments
from app.services.phonemes import (
    compute_phoneme_similarity,
    detect_tamil_confusions,
    phoneme_confidence,
    text_to_ipa,
)

logger = logging.getLogger(__name__)


def _clip_score(value: float) -> float:
    """Clip a score to the 0.0 through 100.0 range.

    Args:
        value: Raw score.

    Returns:
        Clipped score.
    """
    return max(0.0, min(100.0, float(value)))


def _wer(reference: str, hypothesis: str) -> float:
    """Compute word error rate with jiwer fallback.

    Args:
        reference: Reference text.
        hypothesis: Hypothesis text.

    Returns:
        WER value.
    """
    try:
        import jiwer

        return float(jiwer.wer(reference, hypothesis))
    except Exception:
        reference_words = reference.split()
        hypothesis_words = hypothesis.split()
        if not reference_words:
            return 0.0 if not hypothesis_words else 1.0
        similarity = SequenceMatcher(None, reference_words, hypothesis_words).ratio()
        return max(0.0, 1.0 - similarity)


def _cer(reference: str, hypothesis: str) -> float:
    """Compute character error rate with jiwer fallback.

    Args:
        reference: Reference text.
        hypothesis: Hypothesis text.

    Returns:
        CER value.
    """
    try:
        import jiwer

        return float(jiwer.cer(reference, hypothesis))
    except Exception:
        if not reference:
            return 0.0 if not hypothesis else 1.0
        similarity = SequenceMatcher(None, reference, hypothesis).ratio()
        return max(0.0, 1.0 - similarity)


def compute_content_accuracy(reference: str, hypothesis: str) -> float:
    """Compute content accuracy from word error rate.

    Args:
        reference: Reference text.
        hypothesis: Hypothesis text.

    Returns:
        Content accuracy score in [0.0, 100.0].
    """
    return _clip_score((1.0 - _wer(reference, hypothesis)) * 100.0)


def compute_fluency_score(word_segments: Sequence[WordSegment], total_duration: float) -> float:
    """Score fluency from pauses and speaking rate.

    Args:
        word_segments: Word timing segments.
        total_duration: Total speech duration in seconds.

    Returns:
        Fluency score in [0.0, 100.0].
    """
    if total_duration <= 0.0 or not word_segments:
        return 0.0
    sorted_segments = sorted(word_segments, key=lambda item: item.start_time)
    long_pauses = 0
    for previous, current in zip(sorted_segments, sorted_segments[1:]):
        if current.start_time - previous.end_time > 0.5:
            long_pauses += 1
    syllable_estimate = sum(max(1, len(segment.word) // 2) for segment in sorted_segments)
    speaking_rate = syllable_estimate / max(total_duration, 0.001)
    rate_penalty = 0.0
    if speaking_rate < 2.0:
        rate_penalty = (2.0 - speaking_rate) * 12.5
    elif speaking_rate > 6.0:
        rate_penalty = (speaking_rate - 6.0) * 12.5
    return _clip_score(100.0 - (long_pauses * 10.0) - rate_penalty)


def _dtw_score(reference_embeddings: list[np.ndarray], hypothesis_embeddings: list[np.ndarray]) -> float:
    """Convert embedding DTW distance into a score.

    Args:
        reference_embeddings: Reference embedding sequence.
        hypothesis_embeddings: Hypothesis embedding sequence.

    Returns:
        Pronunciation score in [0.0, 100.0].
    """
    if not reference_embeddings or not hypothesis_embeddings:
        return 0.0
    ref = np.vstack(reference_embeddings)
    hyp = np.vstack(hypothesis_embeddings)
    try:
        from dtaidistance import dtw_ndim

        distance = float(dtw_ndim.distance(ref, hyp))
    except Exception as exc:
        logger.warning("DTW dependency failed; using sequence distance fallback: %s", exc)
        length = min(len(ref), len(hyp))
        if length == 0:
            return 0.0
        distance = float(np.linalg.norm(ref[:length] - hyp[:length]) / length)
    return _clip_score(100.0 / (1.0 + distance))


def _phoneme_errors(reference_text: str, hypothesis_text: str) -> list[PhonemeError]:
    """Detect word-level phoneme mismatches.

    Args:
        reference_text: Reference Tamil text.
        hypothesis_text: Hypothesis Tamil text.

    Returns:
        List of phoneme errors.
    """
    errors: list[PhonemeError] = []
    ref_words = reference_text.split()
    hyp_words = hypothesis_text.split()
    max_len = max(len(ref_words), len(hyp_words))
    for index in range(max_len):
        ref_word = ref_words[index] if index < len(ref_words) else ""
        hyp_word = hyp_words[index] if index < len(hyp_words) else ""
        ref_ipa = text_to_ipa(ref_word) if ref_word else ""
        hyp_ipa = text_to_ipa(hyp_word) if hyp_word else ""
        if ref_ipa == hyp_ipa:
            continue
        if not ref_word:
            error_type = "insertion"
            display_word = hyp_word
            ref_ipa = "-"
        elif not hyp_word:
            error_type = "deletion"
            display_word = ref_word
            hyp_ipa = "-"
        else:
            error_type = "substitution"
            display_word = ref_word
        confusions = detect_tamil_confusions(ref_ipa, hyp_ipa, ref_word)
        errors.append(
            PhonemeError(
                word=display_word or "-",
                expected_ipa=ref_ipa or "-",
                actual_ipa=hyp_ipa or "-",
                error_type=error_type,
                tamil_confusion=confusions[0] if confusions else None,
                confidence=phoneme_confidence(ref_ipa, hyp_ipa),
            )
        )
    return errors


def score_pronunciation(
    reference_text: str,
    hypothesis_text: str,
    reference_audio_path: str | None = None,
    hypothesis_audio_path: str | None = None,
) -> PronunciationResult | float:
    """Score pronunciation using text, phonemes, alignment, and embeddings.

    Args:
        reference_text: Reference Tamil text, or expected phonemes for legacy use.
        hypothesis_text: Hypothesis Tamil text, or spoken phonemes for legacy use.
        reference_audio_path: Reference audio path.
        hypothesis_audio_path: Hypothesis audio path.

    Returns:
        PronunciationResult for the full pipeline, or a legacy float score when
        audio paths are omitted.
    """
    if reference_audio_path is None or hypothesis_audio_path is None:
        return round(SequenceMatcher(None, reference_text, hypothesis_text).ratio() * 100.0, 2)

    wer_value = _wer(reference_text, hypothesis_text)
    cer_value = _cer(reference_text, hypothesis_text)
    content_accuracy = compute_content_accuracy(reference_text, hypothesis_text)
    ref_alignment = get_word_segments(align_transcript(reference_audio_path, reference_text))
    hyp_alignment = get_word_segments(align_transcript(hypothesis_audio_path, hypothesis_text))
    total_duration = max((segment.end_time for segment in hyp_alignment), default=0.0)
    fluency_score = compute_fluency_score(hyp_alignment, total_duration)

    reference_embeddings: list[np.ndarray] = []
    hypothesis_embeddings: list[np.ndarray] = []
    for segment in ref_alignment:
        reference_embeddings.append(
            extract_segment_embeddings(reference_audio_path, segment.start_time, segment.end_time)
        )
    for segment in hyp_alignment:
        hypothesis_embeddings.append(
            extract_segment_embeddings(hypothesis_audio_path, segment.start_time, segment.end_time)
        )

    acoustic_score = _dtw_score(reference_embeddings, hypothesis_embeddings)
    ipa_similarity = compute_phoneme_similarity(text_to_ipa(reference_text), text_to_ipa(hypothesis_text)) * 100.0
    pronunciation_accuracy = _clip_score((0.7 * acoustic_score) + (0.3 * ipa_similarity))

    return PronunciationResult(
        content_accuracy=content_accuracy,
        pronunciation_accuracy=pronunciation_accuracy,
        fluency_score=fluency_score,
        phoneme_errors=_phoneme_errors(reference_text, hypothesis_text),
        wer=wer_value,
        cer=cer_value,
    )


def compute_overall_score(pronunciation: float, content_accuracy: float, prosody: float) -> float:
    """Compute the required weighted overall score.

    Args:
        pronunciation: Pronunciation accuracy.
        content_accuracy: Content accuracy.
        prosody: Prosody score.

    Returns:
        Weighted overall score.
    """
    return _clip_score((0.50 * pronunciation) + (0.30 * content_accuracy) + (0.20 * prosody))
