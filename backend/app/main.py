import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.pronunciation import router as pronunciation_router
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
app = FastAPI(title="Tamil Pronunciation API")
GENERATED_AUDIO_DIR = Path(__file__).resolve().parent / "generated_audio"
GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pronunciation_router)
app.mount("/audio", StaticFiles(directory=str(GENERATED_AUDIO_DIR)), name="audio")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request method, path, status, and duration.

    Args:
        request: Incoming FastAPI request.
        call_next: Next ASGI request handler.

    Returns:
        HTTP response from the next handler.
    """
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000.0
    logger.info(
        "%s %s -> %s %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/")
def root():
    """Return root health information.

    Returns:
        Basic API status payload.
    """
    return {"status": "running"}
