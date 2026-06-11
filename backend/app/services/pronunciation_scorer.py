from difflib import SequenceMatcher

def score_pronunciation(
    expected_phonemes: str,
    spoken_phonemes: str
):
    score = SequenceMatcher(
        None,
        expected_phonemes,
        spoken_phonemes
    ).ratio()

    return round(score * 100, 2)