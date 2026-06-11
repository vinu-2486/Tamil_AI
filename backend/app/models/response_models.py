"""
Pydantic models for API responses.
"""

from pydantic import BaseModel
from typing import Optional, List

class PronunciationResponse(BaseModel):
    score: float
    feedback: str
    phoneme_scores: Optional[List[dict]] = None
    suggestions: Optional[List[str]] = None
