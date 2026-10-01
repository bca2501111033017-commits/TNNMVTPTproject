# EduGenie – Google Gemini Powered Learning Assistant

EduGenie is an AI-powered educational assistant for students and self-learners,
built with **FastAPI** (backend) and plain **HTML/CSS/JavaScript** (frontend),
powered by **Google's Gemini API**.

## 1. Features

- **Q&A** – Ask any academic or general educational question and get a concise answer.
- **Concept Explanation** – Get a complex topic explained in simple, beginner-friendly language with an example.
- **Quiz Generation** – Generate a 3-question multiple-choice quiz from a topic or a pasted passage, then take it and see your score.
- **Summarization** – Condense a long educational passage into a short, clear summary.
- **Personalized Learning Path** – Get a Beginner → Intermediate → Advanced roadmap for any topic, with a timeline and learning resources.

## 2. Technology Stack

**Backend:** Python 3.10+, FastAPI, Uvicorn, Jinja2, Pydantic, python-dotenv, Google Gemini API (`google-genai` SDK)

**Frontend:** HTML5, CSS3, Vanilla JavaScript (no frameworks)

## 3. Folder Structure

```
EduGenie/
│
├── main.py                  # FastAPI app and route definitions
├── gemini_service.py        # Centralized Gemini API client + error handling
├── qna.py                   # Module 1: Q&A
├── explanation_module.py    # Module 2: Concept explanation
├── quiz_module.py           # Module 3: Quiz generation
├── summary_module.py        # Module 4: Summarization
├── learning_path.py         # Module 5: Personalized learning path
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── templates/
│   └── index.html           # Single-page frontend
│
├── static/
│   ├── style.css
│   └── script.js
│
└── tests/
    └── test_api.py          # Endpoint tests (Gemini calls are mocked)
```

## 4. Prerequisites

- Python 3.10 or newer installed
- A free Google Gemini API key from https://aistudio.google.com/apikey

## 5. Setup

### 5.1 Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 5.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 5.3 Configure your Gemini API key

Copy the example environment file and edit it:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and paste your key:

```
GEMINI_API_KEY=your_real_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
HOST=127.0.0.1
PORT=8000
```

`.env` is already listed in `.gitignore`, so your key will never be committed.

> **Model note:** `GEMINI_MODEL` is read from a single place (`gemini_service.py`).
> If Google ever renames or retires the default model, just update this one
> line in `.env` — no code changes needed.

## 6. Running the Application

```bash
uvicorn main:app --reload
```

Then open your browser at:

```
http://127.0.0.1:8000
```

## 7. API Endpoints

| Method | Endpoint                  | Description                              |
|--------|----------------------------|-------------------------------------------|
| GET    | `/`                        | Serves the frontend                       |
| GET    | `/health`                  | Health check → `{"status": "ok"}`         |
| POST   | `/qa`                      | Answer a question                         |
| POST   | `/explain`                 | Explain a concept                         |
| POST   | `/quiz`                    | Generate a 3-question multiple-choice quiz|
| POST   | `/summarize`               | Summarize a passage of text               |
| POST   | `/learn/recommendations`   | Generate a personalized learning path     |

### Example requests

**Q&A**
```bash
curl -X POST http://127.0.0.1:8000/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What is photosynthesis?"}'
```

**Explain**
```bash
curl -X POST http://127.0.0.1:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"topic": "Pythagoras Theorem"}'
```

**Quiz (by topic)**
```bash
curl -X POST http://127.0.0.1:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{"topic": "Pythagoras Theorem"}'
```

**Quiz (by text)**
```bash
curl -X POST http://127.0.0.1:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{"text": "Pythagoras theorem states that in a right triangle..."}'
```

**Summarize**
```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "A long educational passage here..."}'
```

**Learning path**
```bash
curl -X POST http://127.0.0.1:8000/learn/recommendations \
  -H "Content-Type: application/json" \
  -d '{"topic": "SQL", "level": "Beginner"}'
```

## 8. Testing

The test suite mocks every Gemini call, so it runs instantly without a live
API key or internet connection.

```bash
pytest
```

This checks:
- `/` and `/health` load correctly
- Every module's success path
- Empty/invalid input is rejected with a friendly error
- The quiz always has exactly 3 questions with exactly 4 options each, and a valid correct answer
- Malformed AI output is handled safely (no server crash)

## 9. Common Errors and Solutions

| Problem | Likely Cause | Solution |
|---|---|---|
| `Gemini API key is missing or invalid` | `.env` not created, or `GEMINI_API_KEY` left blank | Copy `.env.example` to `.env` and add your real key |
| `AI service is temporarily unavailable` | Gemini API had a transient error | Wait a moment and try again |
| `The AI service is receiving too many requests` | You hit Gemini's free-tier rate limit | Wait a minute before generating again |
| Page loads but every action fails | Backend not running, or wrong port | Confirm `uvicorn main:app --reload` is running and you're on `http://127.0.0.1:8000` |
| `ModuleNotFoundError` on startup | Dependencies not installed / wrong virtual environment active | Re-run `pip install -r requirements.txt` inside your activated venv |
| Quiz doesn't appear / shows an error | Gemini returned text that wasn't valid JSON | The backend automatically retries parsing after cleaning Markdown fences; if it still fails, just click Generate again |

## 10. Notes for Viva / Demonstration

- All AI calls go through a single function in `gemini_service.py` — this is the one place to point to when explaining "how EduGenie talks to Gemini."
- The frontend never sees the Gemini API key; it only talks to the FastAPI backend via `fetch()`.
- Every module (`qna.py`, `explanation_module.py`, `quiz_module.py`, `summary_module.py`, `learning_path.py`) is independent and can be explained/demonstrated on its own.
- Run `pytest` live during a viva to show the quiz's structure is validated automatically (3 questions, 4 options, correct answer present).
