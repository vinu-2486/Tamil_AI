from fastapi import APIRouter, UploadFile, File
from app.services.speech_to_text import transcribe
from app.services.feedback_generator import generate_feedback

router = APIRouter(
    prefix="/pronunciation",
    tags=["Pronunciation"]
)

@router.post("/analyze")
async def analyze(audio: UploadFile = File(...)):

    file_path = f"uploads/{audio.filename}"

    with open(file_path, "wb") as f:
        f.write(await audio.read())

    transcript = transcribe(file_path)

    feedback = generate_feedback(transcript)

    return {
        "transcript": transcript,
        "analysis": feedback
    }
