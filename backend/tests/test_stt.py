from app.services.speech_to_text import transcribe

result = transcribe("sample.wav")

print(result)