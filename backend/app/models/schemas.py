"""Pydantic schemas for the pronunciation assessment pipeline."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _score_field() -> float:
    return Field(ge=0.0, le=100.0)


class PhonemeError(BaseModel):
    """Phoneme-level pronunciation error."""

    word: str = Field(min_length=1)
    expected_ipa: str = Field(min_length=1)
    actual_ipa: str = Field(min_length=1)
    error_type: Literal["substitution", "deletion", "insertion"]
    tamil_confusion: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class PronunciationResult(BaseModel):
    """Pronunciation scoring result."""

    content_accuracy: float = _score_field()
    pronunciation_accuracy: float = _score_field()
    fluency_score: float = _score_field()
    phoneme_errors: list[PhonemeError]
    wer: float = Field(ge=0.0)
    cer: float = Field(ge=0.0)

    @field_validator("content_accuracy", "pronunciation_accuracy", "fluency_score")
    @classmethod
    def clip_scores(cls, value: float) -> float:
        """Clamp score values to the API score range."""
        return max(0.0, min(100.0, float(value)))


class ProsodyResult(BaseModel):
    """Prosody analysis result."""

    pitch_mean: float
    pitch_std: float
    pitch_range: float
    speaking_rate_syllables_per_sec: float
    pause_count: int = Field(ge=0)
    pause_duration_total: float = Field(ge=0.0)
    energy_mean: float = Field(ge=0.0)
    prosody_score: float = _score_field()

    @field_validator("prosody_score")
    @classmethod
    def clip_prosody(cls, value: float) -> float:
        """Clamp prosody score to the API score range."""
        return max(0.0, min(100.0, float(value)))


class FeedbackResult(BaseModel):
    """Final pronunciation feedback response."""

    overall_score: float = _score_field()
    pronunciation: float = _score_field()
    fluency: float = _score_field()
    prosody: float = _score_field()
    mistakes: list[PhonemeError]
    feedback: str
    audio_coach_path: str | None = None
