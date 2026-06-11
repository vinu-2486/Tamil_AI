"""
Pydantic models for API requests.
"""

from pydantic import BaseModel
from typing import Optional

class PronunciationRequest(BaseModel):
    lesson_id: Optional[str] = None
    word_id: Optional[str] = None
    user_id: Optional[str] = None
