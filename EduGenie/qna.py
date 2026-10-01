"""
Module 1: Question & Answer

Handles the logic behind the /qa endpoint. A student asks a question and
Gemini answers it in short, clear language.
"""

from pydantic import BaseModel, Field

from gemini_service import generate_text

MAX_QUESTION_LENGTH = 1000


class QuestionRequest(BaseModel):
    """Request body for POST /qa."""
    question: str = Field(..., description="The student's question")


class AnswerResponse(BaseModel):
    """Response body for POST /qa."""
    answer: str


def answer_question(question: str) -> str:
    """Ask Gemini an educational question and return a concise answer."""
    question = (question or "").strip()

    if not question:
        raise ValueError("Please enter a question.")

    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(f"Your question is too long. Please keep it under {MAX_QUESTION_LENGTH} characters.")

    prompt = (
        "You are EduGenie, a friendly and knowledgeable study assistant for "
        "students. Answer the following question clearly and concisely, in "
        "plain language a student can easily understand. Use short bullet "
        "points if that makes the answer easier to follow. Do not pad the "
        "answer with unnecessary filler or repeat the question back.\n\n"
        f"Student's question: {question}"
    )

    return generate_text(prompt)
