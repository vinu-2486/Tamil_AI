"""Acoustic embedding extraction with wav2vec2."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "facebook/wav2vec2-large-xlsr-53"
EMBEDDING_SIZE = 1024
_model_lock = threading.Lock()
_processor = None
_model = None


def _load_model() -> tuple[object, object]:
    """Load wav2vec2 processor and model once.

    Returns:
        Tuple of processor and model instances.

    Raises:
        RuntimeError: If dependencies or model loading fail.
    """
    global _processor, _model
    if _processor is not None and _model is not None:
        return _processor, _model
    with _model_lock:
        if _processor is not None and _model is not None:
            return _processor, _model
        try:
            from transformers import Wav2Vec2Model, Wav2Vec2Processor

            _processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
            _model = Wav2Vec2Model.from_pretrained(MODEL_NAME)
            _model.eval()
            return _processor, _model
        except Exception as exc:
            logger.warning("Unable to load wav2vec2 model: %s", exc)
            raise RuntimeError("Unable to load acoustic model") from exc


def load_audio(audio_path: str, target_sr: int = 16000) -> np.ndarray:
    """Load audio as 16 kHz mono.

    Args:
        audio_path: Path to an audio file.
        target_sr: Target sampling rate.

    Returns:
        Mono waveform as a numpy array.

    Raises:
        FileNotFoundError: If the audio path does not exist.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    import librosa

    audio, _ = librosa.load(path, sr=target_sr, mono=True)
    return np.asarray(audio, dtype=np.float32)


def _zero_embedding() -> np.ndarray:
    """Create a zero embedding vector.

    Returns:
        Numpy vector of zeros.
    """
    return np.zeros((EMBEDDING_SIZE,), dtype=np.float32)


def _embed_audio(audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """Extract a mean-pooled embedding from a waveform.

    Args:
        audio: Mono waveform.
        sample_rate: Audio sampling rate.

    Returns:
        Mean-pooled hidden-state embedding.

    Raises:
        RuntimeError: If model inference fails.
    """
    if audio.size < int(sample_rate * 0.1):
        logger.warning("Audio shorter than 0.1 seconds; returning zero embedding")
        return _zero_embedding()
    try:
        import torch

        processor, model = _load_model()
        inputs = processor(audio, sampling_rate=sample_rate, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze(0).detach().cpu().numpy()
        return np.asarray(embedding, dtype=np.float32)
    except Exception as exc:
        logger.warning("Embedding extraction failed: %s", exc)
        raise RuntimeError("Unable to extract acoustic embeddings") from exc


def extract_embeddings(audio_path: str) -> np.ndarray:
    """Extract an embedding for a full audio file.

    Args:
        audio_path: Path to an audio file.

    Returns:
        Mean-pooled wav2vec2 embedding.
    """
    return _embed_audio(load_audio(audio_path))


def extract_segment_embeddings(audio_path: str, start: float, end: float) -> np.ndarray:
    """Extract an embedding for an audio segment.

    Args:
        audio_path: Path to an audio file.
        start: Segment start time in seconds.
        end: Segment end time in seconds.

    Returns:
        Mean-pooled wav2vec2 embedding for the segment.
    """
    audio = load_audio(audio_path)
    sample_rate = 16000
    start_index = max(0, int(start * sample_rate))
    end_index = min(audio.size, max(start_index, int(end * sample_rate)))
    return _embed_audio(audio[start_index:end_index], sample_rate=sample_rate)


def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Compute cosine similarity normalized to 0.0 through 1.0.

    Args:
        emb1: First embedding.
        emb2: Second embedding.

    Returns:
        Cosine similarity in [0.0, 1.0].
    """
    left = np.asarray(emb1, dtype=np.float32)
    right = np.asarray(emb2, dtype=np.float32)
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 0.0
    cosine = float(np.dot(left, right) / denominator)
    return max(0.0, min(1.0, (cosine + 1.0) / 2.0))


def extract_audio_features(audio_path: str) -> dict[str, float]:
    """Backward-compatible lightweight acoustic features.

    Args:
        audio_path: Path to an audio file.

    Returns:
        Duration, energy, and clarity features.
    """
    import librosa

    audio = load_audio(audio_path)
    duration = librosa.get_duration(y=audio, sr=16000)
    rms = np.mean(librosa.feature.rms(y=audio))
    zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
    return {"duration": float(duration), "energy": float(rms), "clarity": float(zcr)}
