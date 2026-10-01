"""
Module 5: Personalized Learning Path

Handles the logic behind the /learn/recommendations endpoint. Builds a
Beginner -> Intermediate -> Advanced learning path for a topic, including
a timeline and useful resources.
"""

from pydantic import BaseModel, Field

from gemini_service import generate_json, GeminiInvalidResponseError

MAX_TOPIC_LENGTH = 300
VALID_LEVELS = {"beginner", "intermediate", "advanced"}


class LearningPathRequest(BaseModel):
    """Request body for POST /learn/recommendations."""
    topic: str = Field(..., description="The subject the learner wants a path for")
    level: str = Field("Beginner", description="The learner's current level")


def generate_learning_path(topic: str, level: str) -> dict:
    """Ask Gemini to build a structured, leveled learning path for a topic."""
    topic = (topic or "").strip()

    if not topic:
        raise ValueError("Please enter a topic to build a learning path for.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError(f"Topic is too long. Please keep it under {MAX_TOPIC_LENGTH} characters.")

    level = (level or "Beginner").strip() or "Beginner"
    if level.lower() not in VALID_LEVELS:
        level = "Beginner"

    prompt = (
        "You are EduGenie, an assistant that designs personalized learning "
        f"paths. Build a complete learning path for the topic '{topic}', "
        f"tailored to a learner whose current level is '{level}'.\n\n"
        "Return ONLY valid JSON (no Markdown fences, no extra text) that "
        "matches this exact structure:\n"
        "{\n"
        '  "topic": "string",\n'
        '  "current_level": "string",\n'
        '  "stages": [\n'
        "    {\n"
        '      "stage": "Beginner",\n'
        '      "timeline": "e.g. Week 1-2",\n'
        '      "topics": ["string", "string", "string"]\n'
        "    }\n"
        "  ],\n"
        '  "resources": [\n'
        '    {"type": "Video", "title": "string"},\n'
        '    {"type": "Article", "title": "string"},\n'
        '    {"type": "Book", "title": "string"},\n'
        '    {"type": "Documentation", "title": "string"}\n'
        "  ],\n"
        '  "tips": ["string", "string"]\n'
        "}\n\n"
        "Rules:\n"
        "- 'stages' must always contain all three stages, in this exact "
        "order: Beginner, Intermediate, Advanced.\n"
        "- Each stage needs 3 to 5 concrete, topic-specific subtopics and a "
        "realistic timeline.\n"
        "- 'resources' should list 3-6 real, well-known learning resources "
        "relevant to the topic (videos, articles, books, or documentation).\n"
        "- Tailor the pacing and depth to the learner's stated level."
    )

    raw = generate_json(prompt)

    if not isinstance(raw, dict) or not isinstance(raw.get("stages"), list) or not raw.get("stages"):
        raise GeminiInvalidResponseError(
            "The AI produced an incomplete learning path. Please try again."
        )

    raw.setdefault("topic", topic)
    raw.setdefault("current_level", level)
    raw.setdefault("resources", [])
    raw.setdefault("tips", [])

    return raw
