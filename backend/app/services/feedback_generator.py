"""LLM feedback generation for Tamil pronunciation assessment."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import overload

from dotenv import load_dotenv

from app.models.schemas import FeedbackResult, PronunciationResult, ProsodyResult
from app.services.pronunciation_scorer import compute_overall_score
from app.utils.exceptions import FeedbackGenerationError

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Tamil language pronunciation coach.
Analyze the following pronunciation assessment data and provide:
1. Specific errors with Tamil script examples
2. Actionable improvement tips
3. Encouragement based on score
Respond in English. Be concise (under 150 words)."""


def _normalize_feedback_language(feedback_language: str) -> str:
    """Normalize the requested feedback language.

    Args:
        feedback_language: User-selected language value.

    Returns:
        ``english`` or ``tamil``.
    """
    value = feedback_language.strip().lower()
    if value in {"ta", "tam", "tamil"}:
        return "tamil"
    return "english"


def _repeat_tamil_sentence(text: str) -> str:
    """Repeat a Tamil sentence three times for correction practice.

    Args:
        text: Tamil sentence.

    Returns:
        Text repeated three times.
    """
    sentence = text.strip()
    return " ".join([sentence] * 3).strip()


def _fallback_legacy_feedback(transcript: str, feedback_language: str) -> dict[str, object]:
    """Build a safe fallback response for the STT-only endpoint.

    Args:
        transcript: STT transcript.
        feedback_language: Normalized feedback language.

    Returns:
        Dictionary matching the analysis response contract.
    """
    correction_audio_text = _repeat_tamil_sentence(transcript)
    if feedback_language == "tamil":
        return {
            "score": 0,
            "feedback": "கருத்தை உருவாக்க முடியவில்லை.",
            "improvements": ["மீண்டும் முயற்சி செய்யவும்."],
            "coach_audio_text": "கருத்தை உருவாக்க முடியவில்லை. தயவுசெய்து மீண்டும் பதிவு செய்யவும்.",
            "correction_audio_text": correction_audio_text,
        }
    return {
        "score": 0,
        "feedback": "Unable to generate feedback.",
        "improvements": ["Please try again."],
        "coach_audio_text": "Unable to generate feedback. Please record again and try once more.",
        "correction_audio_text": correction_audio_text,
    }


def _legacy_feedback(transcript: str, feedback_language: str = "english") -> dict[str, object]:
    """Generate feedback for the existing STT-only endpoint.

    Args:
        transcript: STT transcript.
        feedback_language: User-selected feedback language.

    Returns:
        Dictionary with score, feedback, and improvements.
    """
    language = _normalize_feedback_language(feedback_language)
    language_instruction = (
        "Write feedback, improvements, and coach_audio_text in Tamil."
        if language == "tamil"
        else "Write feedback, improvements, and coach_audio_text in English."
    )
    prompt = f"""
You are a Tamil pronunciation coach.

Transcript:
{transcript}

Analyze the pronunciation quality.
{language_instruction}

Rules:
- Return ONLY valid JSON.
- correction_audio_text must contain only the corrected Tamil sentence.
- Repeat the corrected Tamil sentence exactly 3 times inside correction_audio_text.
- correction_audio_text must be suitable for Tamil text-to-speech.
- coach_audio_text must summarize pronunciation performance, explain mistakes, and explain improvements.
- coach_audio_text must use the same language as feedback.

Return ONLY valid JSON:

{{
    "score": 85,
    "feedback": "Short feedback sentence in the selected language.",
    "improvements": [
        "Improvement 1",
        "Improvement 2",
        "Improvement 3"
    ],
    "coach_audio_text": "Spoken coach feedback in the selected language.",
    "correction_audio_text": "Corrected Tamil sentence. Corrected Tamil sentence. Corrected Tamil sentence."
}}
"""
    try:
        text = _call_openai(prompt, system_prompt="You are a Tamil pronunciation coach.", model="gpt-5.5")
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        feedback = str(parsed.get("feedback", "")).strip()
        improvements = list(parsed.get("improvements", []))
        coach_audio_text = str(parsed.get("coach_audio_text") or "").strip()
        correction_audio_text = str(parsed.get("correction_audio_text") or "").strip()
        if not coach_audio_text:
            coach_audio_text = f"{feedback} {' '.join(str(item) for item in improvements)}".strip()
        if not correction_audio_text:
            correction_audio_text = _repeat_tamil_sentence(transcript)
        return {
            "score": float(parsed.get("score", 0)),
            "feedback": feedback or ("கருத்து உருவாக்கப்பட்டது." if language == "tamil" else "Feedback generated."),
            "improvements": improvements,
            "coach_audio_text": coach_audio_text,
            "correction_audio_text": correction_audio_text,
        }
    except Exception as exc:
        logger.warning("Legacy feedback generation failed: %s", exc)
        return _fallback_legacy_feedback(transcript, language)


def _call_openai(prompt: str, system_prompt: str = SYSTEM_PROMPT, model: str = "gpt-5.5") -> str:
    """Call the OpenAI-compatible chat API.

    Args:
        prompt: User prompt.
        system_prompt: System prompt.
        model: Model name.

    Returns:
        Plain text model response.

    Raises:
        FeedbackGenerationError: If the API key or call fails.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise FeedbackGenerationError("OPENAI_API_KEY is not configured")
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=os.getenv("BASE_URL") or None)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    """Call Gemini for feedback generation.

    Args:
        prompt: User prompt.

    Returns:
        Plain text model response.

    Raises:
        FeedbackGenerationError: If the API key or call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise FeedbackGenerationError("GEMINI_API_KEY is not configured")
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)
    return str(response.text).strip()


def _build_feedback_prompt(
    pronunciation_result: PronunciationResult,
    prosody_result: ProsodyResult,
    reference_text: str,
    hypothesis_text: str,
) -> str:
    """Build the LLM user prompt.

    Args:
        pronunciation_result: Pronunciation scores.
        prosody_result: Prosody scores.
        reference_text: Reference Tamil text.
        hypothesis_text: Hypothesis Tamil text.

    Returns:
        Prompt text.
    """
    mistakes = [
        f"{error.word}: expected {error.expected_ipa}, heard {error.actual_ipa}"
        for error in pronunciation_result.phoneme_errors[:5]
    ]
    mistake_text = "\n".join(mistakes) if mistakes else "No major phoneme errors detected."
    return f"""
Reference Tamil: {reference_text}
Learner transcript: {hypothesis_text}
Content accuracy: {pronunciation_result.content_accuracy:.1f}
Pronunciation accuracy: {pronunciation_result.pronunciation_accuracy:.1f}
Fluency: {pronunciation_result.fluency_score:.1f}
Prosody: {prosody_result.prosody_score:.1f}
WER: {pronunciation_result.wer:.3f}
CER: {pronunciation_result.cer:.3f}
Mistakes:
{mistake_text}
"""


@overload
def generate_feedback(transcript: str, feedback_language: str = "english") -> dict[str, object]:
    ...


@overload
def generate_feedback(
    pronunciation_result: PronunciationResult,
    prosody_result: ProsodyResult,
    reference_text: str,
    hypothesis_text: str,
    audio_coach_path: str | None = None,
) -> FeedbackResult:
    ...


def generate_feedback(
    pronunciation_result: PronunciationResult | str,
    prosody_result: ProsodyResult | str | None = None,
    reference_text: str | None = None,
    hypothesis_text: str | None = None,
    audio_coach_path: str | None = None,
) -> FeedbackResult | dict[str, object]:
    """Generate pronunciation feedback.

    Args:
        pronunciation_result: PronunciationResult, or transcript for legacy use.
        prosody_result: ProsodyResult for the full pipeline, or language for legacy use.
        reference_text: Reference Tamil text.
        hypothesis_text: Hypothesis transcript.
        audio_coach_path: Optional generated coach audio path.

    Returns:
        FeedbackResult for the full pipeline, or legacy JSON-like dictionary.

    Raises:
        FeedbackGenerationError: If both LLM attempts fail in the full pipeline.
    """
    if isinstance(pronunciation_result, str):
        legacy_language = prosody_result if isinstance(prosody_result, str) else "english"
        return _legacy_feedback(pronunciation_result, legacy_language)
    if prosody_result is None or reference_text is None or hypothesis_text is None:
        raise FeedbackGenerationError("Full feedback generation requires scores and texts")

    prompt = _build_feedback_prompt(pronunciation_result, prosody_result, reference_text, hypothesis_text)
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            feedback = _call_gemini(prompt) if provider == "gemini" else _call_openai(prompt)
            overall = compute_overall_score(
                pronunciation_result.pronunciation_accuracy,
                pronunciation_result.content_accuracy,
                prosody_result.prosody_score,
            )
            return FeedbackResult(
                overall_score=overall,
                pronunciation=pronunciation_result.pronunciation_accuracy,
                fluency=pronunciation_result.fluency_score,
                prosody=prosody_result.prosody_score,
                mistakes=pronunciation_result.phoneme_errors,
                feedback=feedback,
                audio_coach_path=audio_coach_path,
            )
        except Exception as exc:
            last_error = exc
            logger.warning("Feedback generation attempt %s failed: %s", attempt + 1, exc)
            time.sleep(0.25)
    raise FeedbackGenerationError("Unable to generate feedback") from last_error
