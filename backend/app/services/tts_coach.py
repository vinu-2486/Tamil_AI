"""Tamil text-to-speech coach audio generation."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from uuid import uuid4

from app.utils.exceptions import TTSError

logger = logging.getLogger(__name__)


def _default_output_path() -> Path:
    """Create a default temp coach audio path.

    Returns:
        Path for an MP3 file in the system temp directory.
    """
    return Path(tempfile.gettempdir()) / f"coach_{uuid4().hex}.mp3"


def generate_coach_audio(
    tamil_text: str,
    output_path: str | None = None,
    slow: bool = True,
) -> str:
    """Generate Tamil coach pronunciation audio.

    Args:
        tamil_text: Tamil text to synthesize.
        output_path: Optional output MP3 path.
        slow: Whether gTTS should generate slower practice audio.

    Returns:
        Path to the generated MP3 file.

    Raises:
        TTSError: If gTTS fails or text is empty.
    """
    if not tamil_text.strip():
        raise TTSError("Tamil text must not be empty")
    path = Path(output_path) if output_path else _default_output_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from gtts import gTTS

        tts = gTTS(text=tamil_text, lang="ta", slow=slow)
        tts.save(str(path))
        return str(path)
    except Exception as exc:
        logger.warning("Tamil TTS generation failed: %s", exc)
        raise TTSError("Unable to generate Tamil coach audio") from exc


def generate_word_audio(word: str) -> str:
    """Generate coach audio for a single Tamil word.

    Args:
        word: Tamil word to synthesize.

    Returns:
        Path to the generated MP3 file.

    Raises:
        TTSError: If generation fails.
    """
    return generate_coach_audio(word)


def cleanup_temp_files(paths: list[str]) -> None:
    """Delete generated temporary files.

    Args:
        paths: File paths to remove.

    Returns:
        None.
    """
    for item in paths:
        try:
            path = Path(item)
            if path.exists():
                path.unlink()
        except Exception as exc:
            logger.warning("Unable to delete temporary file %s: %s", item, exc)
