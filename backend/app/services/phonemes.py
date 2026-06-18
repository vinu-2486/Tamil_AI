"""Tamil text to IPA and phoneme utilities."""

from __future__ import annotations

import logging
import math
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)

TAMIL_CONFUSIONS: dict[str, tuple[str, str, str]] = {
    "ழ": ("ɻ", "l", "ழ→ல"),
    "ள": ("ɭ", "l", "ள→ல"),
    "ற": ("r", "ɾ", "ற→ர"),
    "ண": ("ɳ", "n", "ண→ந"),
    "ஞ": ("ɲ", "n", "ஞ→ந"),
    "ங": ("ŋ", "k", "ங→க"),
}

_epi_lock = threading.Lock()
_distance_lock = threading.Lock()


@lru_cache(maxsize=1)
def _get_epitran() -> object | None:
    """Load the Epitran Tamil transliterator once.

    Returns:
        The Epitran instance, or None when the dependency is unavailable.
    """
    with _epi_lock:
        try:
            import epitran

            return epitran.Epitran("tam-Taml")
        except Exception as exc:
            logger.warning("Unable to load Epitran Tamil transliterator: %s", exc)
            return None


@lru_cache(maxsize=1)
def _get_distance() -> object | None:
    """Load the Panphon distance helper once.

    Returns:
        The Panphon Distance instance, or None when unavailable.
    """
    with _distance_lock:
        try:
            from panphon.distance import Distance

            return Distance()
        except Exception as exc:
            logger.warning("Unable to load Panphon distance helper: %s", exc)
            return None


def text_to_ipa(tamil_text: str) -> str:
    """Convert Tamil Unicode text to an IPA string.

    Args:
        tamil_text: Tamil text to transliterate.

    Returns:
        IPA string. If transliteration is unavailable, the input is returned.

    Raises:
        ValueError: If tamil_text is empty.
    """
    if not tamil_text or not tamil_text.strip():
        raise ValueError("Tamil text must not be empty")
    epi = _get_epitran()
    if epi is None:
        return tamil_text.strip()
    try:
        transliterate = getattr(epi, "transliterate")
        return str(transliterate(tamil_text)).strip()
    except UnicodeError as exc:
        logger.warning("Encoding issue while transliterating Tamil text: %s", exc)
        return tamil_text.strip()
    except Exception as exc:
        logger.warning("Unable to transliterate Tamil text: %s", exc)
        return tamil_text.strip()


def get_phoneme_list(ipa_string: str) -> list[str]:
    """Split an IPA string into phoneme tokens.

    Args:
        ipa_string: IPA text to segment.

    Returns:
        A list of phoneme tokens.
    """
    if not ipa_string:
        return []
    distance = _get_distance()
    try:
        ipa_segs = getattr(distance, "ipa_segs")
        return [str(seg) for seg in ipa_segs(ipa_string) if str(seg).strip()]
    except Exception:
        return [char for char in ipa_string if not char.isspace()]


def compute_phoneme_similarity(ipa1: str, ipa2: str) -> float:
    """Compute normalized phoneme similarity between two IPA strings.

    Args:
        ipa1: First IPA string.
        ipa2: Second IPA string.

    Returns:
        Similarity in the range 0.0 to 1.0.
    """
    if ipa1 == ipa2:
        return 1.0
    if not ipa1 or not ipa2:
        return 0.0
    distance = _get_distance()
    try:
        raw_distance = float(distance.hamming_feature_edit_distance(ipa1, ipa2))
        normalizer = max(len(get_phoneme_list(ipa1)), len(get_phoneme_list(ipa2)), 1)
        return max(0.0, min(1.0, 1.0 - (raw_distance / (normalizer * 24.0))))
    except Exception as exc:
        logger.warning("Panphon similarity failed; using character fallback: %s", exc)
        matches = sum(1 for left, right in zip(ipa1, ipa2) if left == right)
        denominator = max(len(ipa1), len(ipa2), 1)
        return max(0.0, min(1.0, matches / denominator))


def detect_tamil_confusions(
    expected_ipa: str,
    actual_ipa: str,
    original_tamil: str,
) -> list[str]:
    """Detect known Tamil phoneme substitutions.

    Args:
        expected_ipa: Reference IPA.
        actual_ipa: Learner IPA.
        original_tamil: Reference Tamil text.

    Returns:
        Confusion labels such as ``ழ→ல``.
    """
    found: list[str] = []
    for tamil_char, (expected, actual, label) in TAMIL_CONFUSIONS.items():
        if tamil_char in original_tamil and expected in expected_ipa and actual in actual_ipa:
            found.append(label)
    return found


def phoneme_confidence(expected_ipa: str, actual_ipa: str) -> float:
    """Return a rounded confidence score for an IPA mismatch.

    Args:
        expected_ipa: Reference IPA.
        actual_ipa: Learner IPA.

    Returns:
        Confidence in the range 0.0 to 1.0.
    """
    similarity = compute_phoneme_similarity(expected_ipa, actual_ipa)
    confidence = 1.0 - similarity
    if math.isclose(confidence, 0.0, abs_tol=1e-9):
        return 0.0
    return round(max(0.0, min(1.0, confidence)), 3)


def text_to_phonemes(text: str) -> str:
    """Backward-compatible alias for the original phoneme helper.

    Args:
        text: Tamil text to convert.

    Returns:
        IPA transcription.
    """
    return text_to_ipa(text)
