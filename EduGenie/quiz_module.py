"""
Module 3: Quiz Generation

Handles the logic behind the /quiz endpoint. Generates exactly 3
multiple-choice questions (4 options each, 1 correct answer) from either a
topic or a passage of educational text.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from gemini_service import generate_json, GeminiInvalidResponseError

MAX_TEXT_LENGTH = 6000
MAX_TOPIC_LENGTH = 300


class QuizRequest(BaseModel):
    """
    Request body for POST /quiz.

    The frontend can send EITHER a topic OR a passage of text - not both are
    required, but at least one must be provided.
    """
    topic: Optional[str] = None
    text: Optional[str] = None

    @model_validator(mode="after")
    def check_topic_or_text(self):
        topic = (self.topic or "").strip()
        text = (self.text or "").strip()

        if not topic and not text:
            raise ValueError("Please provide either a topic or some text for the quiz.")

        if topic and len(topic) > MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic is too long. Please keep it under {MAX_TOPIC_LENGTH} characters.")

        if text and len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text is too long. Please keep it under {MAX_TEXT_LENGTH} characters.")

        return self


class QuizQuestion(BaseModel):
    """A single multiple-choice quiz question."""
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: str

    @model_validator(mode="after")
    def check_correct_answer_in_options(self):
        if self.correct_answer not in self.options:
            raise ValueError("correct_answer must exactly match one of the options.")
        return self


class QuizResponse(BaseModel):
    """Response body for POST /quiz - always exactly 3 questions."""
    questions: List[QuizQuestion] = Field(..., min_length=3, max_length=3)


def generate_quiz(topic: Optional[str], text: Optional[str]) -> dict:
    """Generate a 3-question multiple-choice quiz using Gemini."""
    topic = (topic or "").strip()
    text = (text or "").strip()

    if not topic and not text:
        raise ValueError("Please provide either a topic or some text for the quiz.")

    if text:
        source_description = f"the following educational text:\n\n{text}"
    else:
        source_description = f"the topic: {topic}"

    prompt = (
        "You are EduGenie, an assistant that creates short quizzes for "
        f"students. Create EXACTLY 3 multiple-choice questions based on "
        f"{source_description}\n\n"
        "Rules you MUST follow exactly:\n"
        "1. Return ONLY valid JSON. No Markdown code fences, no extra text "
        "before or after the JSON.\n"
        "2. The JSON must match this exact structure:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "string",\n'
        '      "options": ["string", "string", "string", "string"],\n'
        '      "correct_answer": "string"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "3. There must be exactly 3 questions in the array.\n"
        "4. Each question must have exactly 4 options.\n"
        "5. 'correct_answer' must be an exact copy of one of that question's "
        "4 options.\n"
        "6. Make the incorrect options plausible, not obviously wrong.\n"
        "7. Base every question directly on the supplied topic or text."
    )

    raw = generate_json(prompt)

    try:
        quiz = QuizResponse.model_validate(raw)
    except Exception as exc:
        raise GeminiInvalidResponseError(
            "The AI produced a quiz that didn't match the expected format. Please try again."
        ) from exc

    return quiz.model_dump()
