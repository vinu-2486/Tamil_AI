import epitran

print("Loading Epitran...")

epi = epitran.Epitran("tam-Taml")

print("Epitran loaded successfully")

def text_to_phonemes(text: str):
    return epi.transliterate(text)