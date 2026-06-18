"""FastAPI routes for Tamil pronunciation assessment."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Body, File, Form, HTTPException, UploadFile

from app.models.schemas import FeedbackResult, ProsodyResult
from app.services.feedback_generator import generate_feedback
from app.services.phonemes import get_phoneme_list, text_to_ipa
from app.services.pronunciation_scorer import score_pronunciation
from app.services.prosody_scorer import extract_prosody_features
from app.services.speech_to_text import transcribe
from app.services.tts_coach import cleanup_temp_files, generate_coach_audio
from app.utils.exceptions import FeedbackGenerationError, PronunciationServiceError, TTSError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pronunciation", tags=["Pronunciation"])
GENERATED_AUDIO_DIR = Path(__file__).resolve().parents[1] / "generated_audio"
GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


async def _save_upload(audio_file: UploadFile) -> str:
    """Save an uploaded audio file to a temporary path.

    Args:
        audio_file: Uploaded audio file.

    Returns:
        Saved temporary file path.

    Raises:
        HTTPException: If validation or saving fails.
    """
    suffix = Path(audio_file.filename or "").suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".webm"}:
        raise HTTPException(status_code=422, detail="Audio file must be .wav, .mp3, .m4a, or .webm")
    path = Path(tempfile.gettempdir()) / f"upload_{uuid4().hex}{suffix}"
    try:
        import aiofiles

        async with aiofiles.open(path, "wb") as output:
            while chunk := await audio_file.read(1024 * 1024):
                await output.write(chunk)
    except ModuleNotFoundError:
        logger.warning("aiofiles is not installed; falling back to synchronous upload save")
        path.write_bytes(await audio_file.read())
    except Exception as exc:
        logger.exception("Unable to save uploaded audio")
        raise HTTPException(status_code=500, detail="Unable to save uploaded audio") from exc
    return str(path)


def _normalize_feedback_language(feedback_language: str) -> str:
    """Normalize the requested feedback language.

    Args:
        feedback_language: User-selected feedback language.

    Returns:
        Normalized language name.
    """
    return "tamil" if feedback_language.strip().lower() in {"ta", "tam", "tamil"} else "english"


def _audio_url(filename: str) -> str:
    """Build the public URL for a generated audio file.

    Args:
        filename: Generated MP3 filename.

    Returns:
        Public audio path.
    """
    return f"/audio/{filename}"


def _generate_tamil_audio_url(text: str, prefix: str, slow: bool = True) -> str | None:
    """Generate Tamil MP3 audio and return its public URL.

    Args:
        text: Tamil text to synthesize.
        prefix: Filename prefix.
        slow: Whether to generate slower practice audio.

    Returns:
        Public URL when generation succeeds, otherwise None.
    """
    if not text.strip():
        return None
    filename = f"{prefix}_{uuid4().hex}.mp3"
    output_path = GENERATED_AUDIO_DIR / filename
    try:
        generate_coach_audio(text, str(output_path), slow=slow)
        return _audio_url(filename)
    except TTSError as exc:
        logger.warning("Unable to generate %s Tamil audio: %s", prefix, exc)
        return None


@router.post("/analyze")
async def analyze(
    audio: UploadFile = File(...),
    feedback_language: str = Form("english"),
) -> dict[str, object]:
    """Preserve the existing STT-first analysis endpoint.

    Args:
        audio: Uploaded learner audio.
        feedback_language: User-selected feedback language.

    Returns:
        Existing response shape with transcript and analysis.
    """
    upload_path = await _save_upload(audio)
    try:
        transcript = transcribe(upload_path)
        feedback = generate_feedback(transcript, feedback_language)
        if isinstance(feedback, dict):
            language = _normalize_feedback_language(feedback_language)
            coach_audio_text = str(feedback.get("coach_audio_text") or "")
            correction_audio_text = str(feedback.get("correction_audio_text") or "")
            feedback["coach_audio_url"] = (
                _generate_tamil_audio_url(coach_audio_text, "coach", slow=False)
                if language == "tamil"
                else None
            )
            feedback["correction_audio_url"] = _generate_tamil_audio_url(
                correction_audio_text,
                "correction",
                slow=True,
            )
        return {"transcript": transcript, "analysis": feedback}
    finally:
        cleanup_temp_files([upload_path])


@router.post("/assess", response_model=FeedbackResult)
async def assess_pronunciation(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    language: str = Form("ta"),
) -> FeedbackResult:
    """Assess Tamil pronunciation after STT.

    Args:
        background_tasks: FastAPI background cleanup task manager.
        audio_file: Learner audio upload.
        reference_text: Reference Tamil Unicode text.
        language: Language code, currently expected to be Tamil.

    Returns:
        Full feedback result.

    Raises:
        HTTPException: For bad input or service failures.
    """
    if language != "ta":
        raise HTTPException(status_code=422, detail="Only Tamil language code 'ta' is supported")
    if not reference_text.strip():
        raise HTTPException(status_code=422, detail="reference_text must not be empty")

    upload_path = await _save_upload(audio_file)
    background_tasks.add_task(cleanup_temp_files, [upload_path])
    try:
        hypothesis_text = transcribe(upload_path)
        coach_audio_path = generate_coach_audio(reference_text)
        pronunciation_result = score_pronunciation(
            reference_text,
            hypothesis_text,
            coach_audio_path,
            upload_path,
        )
        prosody_result = extract_prosody_features(upload_path)
        return generate_feedback(
            pronunciation_result,
            prosody_result,
            reference_text,
            hypothesis_text,
            audio_coach_path=coach_audio_path,
        )
    except (TTSError, FeedbackGenerationError, PronunciationServiceError) as exc:
        logger.exception("Pronunciation assessment failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected pronunciation assessment failure")
        raise HTTPException(status_code=500, detail="Pronunciation assessment failed") from exc


@router.post("/phonemes")
async def phonemes(payload: dict[str, str] = Body(...)) -> dict[str, object]:
    """Convert Tamil text to IPA and phonemes.

    Args:
        payload: JSON body containing a text field.

    Returns:
        IPA string and phoneme list.

    Raises:
        HTTPException: If text is missing.
    """
    text = payload.get("text", "")
    if not text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")
    ipa = text_to_ipa(text)
    return {"ipa": ipa, "phonemes": get_phoneme_list(ipa)}


@router.post("/prosody", response_model=ProsodyResult)
async def prosody(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
) -> ProsodyResult:
    """Analyze prosody for uploaded audio.

    Args:
        background_tasks: FastAPI background cleanup task manager.
        audio_file: Uploaded audio file.

    Returns:
        Prosody result.
    """
    upload_path = await _save_upload(audio_file)
    background_tasks.add_task(cleanup_temp_files, [upload_path])
    try:
        return extract_prosody_features(upload_path)
    except Exception as exc:
        logger.exception("Prosody analysis failed")
        raise HTTPException(status_code=500, detail="Prosody analysis failed") from exc


@router.get("/health")
async def health() -> dict[str, object]:
    """Report pronunciation router health.

    Returns:
        Health status payload.
    """
    return {"status": "ok", "models_loaded": False}
