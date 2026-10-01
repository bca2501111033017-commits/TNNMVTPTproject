"""
EduGenie - Google Gemini Powered Learning Assistant
=====================================================

Main FastAPI application. This file wires together the frontend, the five
AI modules, and consistent error handling. Run it with:

    uvicorn main:app --reload

Then open http://127.0.0.1:8000 in your browser.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import qna
import explanation_module
import quiz_module
import summary_module
import learning_path
from gemini_service import (
    GeminiServiceError,
    MissingAPIKeyError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edugenie")

app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Simple request models for the endpoints that only need one field
# (Quiz and Learning Path use the richer models defined in their own modules)
# ---------------------------------------------------------------------------
class QARequest(BaseModel):
    question: str = Field(..., description="The student's question")


class ExplainRequest(BaseModel):
    topic: str = Field(..., description="The concept to explain")


class SummarizeRequest(BaseModel):
    text: str = Field(..., description="The text to summarize")


# ---------------------------------------------------------------------------
# Consistent, friendly error handling
# ---------------------------------------------------------------------------
def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


def _handle_service_error(exc: Exception) -> JSONResponse:
    """Map any exception raised by a module into a safe JSON error response."""
    if isinstance(exc, ValueError):
        # Input validation problems raised by our own modules (safe to show).
        return _error_response(400, str(exc))

    if isinstance(exc, MissingAPIKeyError):
        logger.error("Gemini API key problem: %s", exc)
        return _error_response(
            500, "Gemini API key is missing or invalid. Please contact the administrator."
        )

    if isinstance(exc, GeminiRateLimitError):
        return _error_response(429, str(exc))

    if isinstance(exc, GeminiTimeoutError):
        return _error_response(504, str(exc))

    if isinstance(exc, GeminiServiceError):
        logger.error("Gemini service error: %s", exc)
        return _error_response(502, "AI service is temporarily unavailable. Please try again.")

    # Anything else is an unexpected bug - log the real details, but never
    # show a stack trace or internal message to the user.
    logger.exception("Unexpected server error")
    return _error_response(500, "Something went wrong on the server. Please try again.")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Turn Pydantic's default validation errors into a friendly message."""
    errors = exc.errors()
    if errors:
        message = str(errors[0].get("msg", "Invalid input."))
        message = message.replace("Value error, ", "")
    else:
        message = "Invalid input."
    return _error_response(400, message)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def home(request: Request):
    """Serve the EduGenie single-page frontend."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/health")
async def health():
    """Simple health check used by the test suite and for monitoring."""
    return {"status": "ok"}


@app.post("/qa")
async def qa_endpoint(payload: QARequest):
    """Module 1: answer an educational question."""
    try:
        answer = qna.answer_question(payload.question)
        return {"answer": answer}
    except Exception as exc:  # noqa: BLE001 - centrally classified
        return _handle_service_error(exc)


@app.post("/explain")
async def explain_endpoint(payload: ExplainRequest):
    """Module 2: explain a concept in simple language."""
    try:
        explanation = explanation_module.explain_concept(payload.topic)
        return {"explanation": explanation}
    except Exception as exc:  # noqa: BLE001
        return _handle_service_error(exc)


@app.post("/quiz")
async def quiz_endpoint(payload: quiz_module.QuizRequest):
    """Module 3: generate a 3-question multiple-choice quiz."""
    try:
        quiz = quiz_module.generate_quiz(payload.topic, payload.text)
        return quiz
    except Exception as exc:  # noqa: BLE001
        return _handle_service_error(exc)


@app.post("/summarize")
async def summarize_endpoint(payload: SummarizeRequest):
    """Module 4: summarize a passage of educational text."""
    try:
        summary = summary_module.summarize_text(payload.text)
        return {"summary": summary}
    except Exception as exc:  # noqa: BLE001
        return _handle_service_error(exc)


@app.post("/learn/recommendations")
async def learning_path_endpoint(payload: learning_path.LearningPathRequest):
    """Module 5: build a personalized Beginner -> Advanced learning path."""
    try:
        path = learning_path.generate_learning_path(payload.topic, payload.level)
        return path
    except Exception as exc:  # noqa: BLE001
        return _handle_service_error(exc)
