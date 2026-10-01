"""
Basic tests for the EduGenie FastAPI application.

These tests mock every call to Gemini, so they run instantly and do not
need a real GEMINI_API_KEY or an internet connection.
"""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Make sure "main" and the other project modules can be imported when tests
# are run from the project root with `pytest`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402

client = TestClient(main.app)


# ---------------------------------------------------------------------------
# Basic routes
# ---------------------------------------------------------------------------
def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "EduGenie" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /qa
# ---------------------------------------------------------------------------
def test_qa_success():
    with patch("qna.generate_text", return_value="The Pacific Ocean is the largest ocean."):
        response = client.post("/qa", json={"question": "Which is the largest ocean?"})
    assert response.status_code == 200
    assert "Pacific" in response.json()["answer"]


def test_qa_empty_question_is_rejected():
    response = client.post("/qa", json={"question": "   "})
    assert response.status_code == 400
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# /explain
# ---------------------------------------------------------------------------
def test_explain_success():
    with patch("explanation_module.generate_text", return_value="A simple explanation."):
        response = client.post("/explain", json={"topic": "Pythagoras Theorem"})
    assert response.status_code == 200
    assert "explanation" in response.json()


def test_explain_empty_topic_is_rejected():
    response = client.post("/explain", json={"topic": ""})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# /quiz
# ---------------------------------------------------------------------------
SAMPLE_QUIZ_JSON = {
    "questions": [
        {
            "question": f"Sample question {i}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
        }
        for i in range(3)
    ]
}


def test_quiz_success_has_three_questions_four_options_each():
    with patch("quiz_module.generate_json", return_value=SAMPLE_QUIZ_JSON):
        response = client.post("/quiz", json={"topic": "Pythagoras Theorem"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    for question in data["questions"]:
        assert len(question["options"]) == 4
        assert question["correct_answer"] in question["options"]


def test_quiz_missing_topic_and_text_is_rejected():
    response = client.post("/quiz", json={})
    assert response.status_code == 400


def test_quiz_invalid_ai_json_is_handled_safely():
    bad_quiz = {"questions": [{"question": "Q1?", "options": ["A", "B"], "correct_answer": "A"}]}
    with patch("quiz_module.generate_json", return_value=bad_quiz):
        response = client.post("/quiz", json={"topic": "Anything"})
    assert response.status_code == 502
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# /summarize
# ---------------------------------------------------------------------------
def test_summarize_success():
    with patch("summary_module.generate_text", return_value="Short summary."):
        response = client.post("/summarize", json={"text": "A long educational passage " * 20})
    assert response.status_code == 200
    assert "summary" in response.json()


def test_summarize_empty_text_is_rejected():
    response = client.post("/summarize", json={"text": ""})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# /learn/recommendations
# ---------------------------------------------------------------------------
SAMPLE_PATH_JSON = {
    "topic": "SQL",
    "current_level": "Beginner",
    "stages": [
        {"stage": "Beginner", "timeline": "Week 1-2", "topics": ["Intro to SQL", "SELECT statements"]},
        {"stage": "Intermediate", "timeline": "Week 3-4", "topics": ["JOINs", "GROUP BY"]},
        {"stage": "Advanced", "timeline": "Week 5-6", "topics": ["Query optimization", "Indexing"]},
    ],
    "resources": [{"type": "Video", "title": "SQL basics"}],
    "tips": ["Practice daily"],
}


def test_learning_path_success():
    with patch("learning_path.generate_json", return_value=SAMPLE_PATH_JSON):
        response = client.post("/learn/recommendations", json={"topic": "SQL", "level": "Beginner"})
    assert response.status_code == 200
    data = response.json()
    stage_names = [s["stage"] for s in data["stages"]]
    assert stage_names == ["Beginner", "Intermediate", "Advanced"]


def test_learning_path_missing_topic_is_rejected():
    response = client.post("/learn/recommendations", json={"topic": ""})
    assert response.status_code == 400
