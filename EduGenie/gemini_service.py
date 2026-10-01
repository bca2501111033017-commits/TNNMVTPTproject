"""
Centralized Gemini AI service for EduGenie.

Every module that needs to talk to Google's Gemini API goes through this
ONE file. That way there is a single place that knows how to call Gemini,
and if Google ever changes the SDK or model name, we only need to update
it here instead of in five different modules.
"""

import os
import re
import json
import logging

from dotenv import load_dotenv

# Load variables from a .env file (if one exists) into the environment.
load_dotenv()

logger = logging.getLogger("edugenie.gemini")

# ---------------------------------------------------------------------------
# Configuration (kept in one place so it is easy to change later)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# "gemini-3.1-flash-lite" is a fast, low-cost, currently-stable Gemini model.
# If Google renames/retires it in the future, just change this default (or,
# better, change GEMINI_MODEL in your .env file) - nothing else needs to change.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()

# Try to import the official Gemini SDK. If it isn't installed yet, we still
# want the rest of the app (and the test suite) to import successfully, so we
# fail gracefully here and only raise a clear error when Gemini is actually
# called.
try:
    from google import genai
    _SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only if the SDK is missing
    genai = None
    _SDK_AVAILABLE = False


# ---------------------------------------------------------------------------
# Custom exceptions - every module in this project catches these instead of
# raw SDK exceptions, so error handling stays consistent everywhere.
# ---------------------------------------------------------------------------
class GeminiServiceError(Exception):
    """Base error for anything that goes wrong while talking to Gemini."""


class MissingAPIKeyError(GeminiServiceError):
    """Raised when GEMINI_API_KEY is missing, empty, or rejected by Google."""


class GeminiTimeoutError(GeminiServiceError):
    """Raised when the request to Gemini takes too long."""


class GeminiRateLimitError(GeminiServiceError):
    """Raised when Gemini reports we are sending requests too fast (quota/429)."""


class GeminiInvalidResponseError(GeminiServiceError):
    """Raised when Gemini returns something empty or malformed."""


_client = None  # created once, reused for every request


def _get_client():
    """Create (once) and return the Gemini client."""
    global _client

    if not _SDK_AVAILABLE:
        raise GeminiServiceError(
            "The 'google-genai' package is not installed. "
            "Run: pip install -r requirements.txt"
        )

    if not GEMINI_API_KEY:
        raise MissingAPIKeyError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add "
            "your Gemini API key."
        )

    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)

    return _client


def generate_text(prompt: str) -> str:
    """
    Send `prompt` to Gemini and return the plain text response.

    Raises a GeminiServiceError subclass on any failure so callers can show
    a friendly message instead of the server crashing.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    client = _get_client()

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
    except GeminiServiceError:
        raise
    except Exception as exc:  # noqa: BLE001 - classified below into friendly errors
        raise _classify_exception(exc) from exc

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise GeminiInvalidResponseError("Gemini returned an empty response. Please try again.")

    return text.strip()


def generate_json(prompt: str) -> dict:
    """
    Send `prompt` to Gemini and parse the response as JSON.

    Handles the common case where Gemini wraps its JSON reply in a Markdown
    code fence, e.g. ```json { ... } ```.
    """
    raw_text = generate_text(prompt)
    cleaned = _strip_markdown_fence(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse Gemini JSON response: %s", cleaned[:500])
        raise GeminiInvalidResponseError(
            "The AI returned a response that could not be understood. Please try again."
        ) from exc


def _strip_markdown_fence(text: str) -> str:
    """Remove a ```json ... ``` or ``` ... ``` wrapper if Gemini added one."""
    text = text.strip()
    fence_pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    match = re.match(fence_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def _classify_exception(exc: Exception) -> GeminiServiceError:
    """Turn a raw SDK/network exception into one of our friendly errors."""
    message = str(exc).lower()

    if "timeout" in message or "timed out" in message or "deadline" in message:
        return GeminiTimeoutError("The request to the AI service timed out. Please try again.")

    if "429" in message or "rate" in message or "quota" in message or "resource_exhausted" in message:
        return GeminiRateLimitError(
            "The AI service is receiving too many requests right now. Please wait a moment and try again."
        )

    if "api key" in message or "api_key" in message or "401" in message or "403" in message or "permission" in message:
        return MissingAPIKeyError(
            "The Gemini API key was rejected. Check GEMINI_API_KEY in your .env file."
        )

    if "404" in message or "not found" in message:
        return GeminiServiceError(
            f"The Gemini model '{GEMINI_MODEL}' was not found or is unavailable. "
            "Check GEMINI_MODEL in your .env file."
        )

    if "connection" in message or "network" in message or "resolve" in message:
        return GeminiServiceError("Could not connect to the Gemini API. Check your internet connection.")

    return GeminiServiceError("The AI service returned an unexpected error. Please try again.")
