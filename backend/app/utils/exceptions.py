"""Custom exceptions for pronunciation services."""


class PronunciationServiceError(Exception):
    """Base exception for pronunciation assessment failures."""


class AlignmentError(PronunciationServiceError):
    """Raised when transcript alignment fails."""


class TTSError(PronunciationServiceError):
    """Raised when coach text-to-speech generation fails."""


class FeedbackGenerationError(PronunciationServiceError):
    """Raised when LLM feedback generation fails."""
