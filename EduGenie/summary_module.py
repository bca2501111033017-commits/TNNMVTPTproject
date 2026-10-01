"""
Module 4: Summarization

Handles the logic behind the /summarize endpoint. Condenses a large piece
of educational text into a short, easy-to-read summary.
"""

from pydantic import BaseModel, Field

from gemini_service import generate_text

MAX_TEXT_LENGTH = 12000


class SummarizeRequest(BaseModel):
    """Request body for POST /summarize."""
    text: str = Field(..., description="The educational text to summarize")


class SummaryResponse(BaseModel):
    """Response body for POST /summarize."""
    summary: str


def summarize_text(text: str) -> str:
    """Ask Gemini to summarize a passage of educational text."""
    text = (text or "").strip()

    if not text:
        raise ValueError("Please paste some text to summarize.")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text is too long. Please keep it under {MAX_TEXT_LENGTH} characters.")

    prompt = (
        "You are EduGenie, a study assistant. Summarize the following "
        "educational text for a student. Keep the important facts, remove "
        "repetition and filler, and use short bullet points where that "
        "improves readability. The summary should be noticeably shorter "
        "than the original text while staying accurate.\n\n"
        f"Text to summarize:\n{text}"
    )

    return generate_text(prompt)
