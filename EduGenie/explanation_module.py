"""
Module 2: Concept Explanation

Handles the logic behind the /explain endpoint. Explains a difficult topic
in simple, beginner-friendly language with an example and key points.
"""

from pydantic import BaseModel, Field

from gemini_service import generate_text

MAX_TOPIC_LENGTH = 300


class ExplainRequest(BaseModel):
    """Request body for POST /explain."""
    topic: str = Field(..., description="The concept the student wants explained")


class ExplanationResponse(BaseModel):
    """Response body for POST /explain."""
    explanation: str


def explain_concept(topic: str) -> str:
    """Ask Gemini to explain a concept in simple, beginner-friendly language."""
    topic = (topic or "").strip()

    if not topic:
        raise ValueError("Please enter a topic to explain.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError(f"Topic is too long. Please keep it under {MAX_TOPIC_LENGTH} characters.")

    prompt = (
        "You are EduGenie, a friendly tutor who explains difficult concepts "
        "in simple language. Explain the following concept to a complete "
        "beginner. Avoid unnecessary technical jargon. Structure your reply "
        "using short Markdown-style sections, in this order:\n"
        "1. A short, simple explanation (2-4 sentences)\n"
        "2. A simple real-world example\n"
        "3. Key formula or key points, as bullet points, only if relevant\n\n"
        f"Concept to explain: {topic}"
    )

    return generate_text(prompt)
