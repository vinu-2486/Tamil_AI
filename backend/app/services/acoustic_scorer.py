import librosa
import numpy as np


def extract_audio_features(audio_path):

    audio, sr = librosa.load(
        audio_path,
        sr=16000
    )

    duration = librosa.get_duration(y=audio, sr=sr)

    rms = np.mean(
        librosa.feature.rms(y=audio)
    )

    zcr = np.mean(
        librosa.feature.zero_crossing_rate(audio)
    )

    return {
        "duration": float(duration),
        "energy": float(rms),
        "clarity": float(zcr)
    }