# 🤖 AI Code Review Agent

> An end-to-end AI-powered code review system that automatically reviews Pull Requests using LLMs, GitHub Webhooks, and AST-based code analysis.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![LLM](https://img.shields.io/badge/LLM-Llama_3.3_70B-orange?style=flat-square)
![GitHub Webhooks](https://img.shields.io/badge/GitHub-Webhooks-black?style=flat-square&logo=github)

---

## 🎯 What It Does

Every time a Pull Request is opened or updated, this system:

1. **Receives** a GitHub webhook event
2. **Fetches** the raw diff from GitHub API
3. **Parses** the diff into structured hunks
4. **Analyzes** the code using Python AST (Abstract Syntax Tree)
5. **Builds** rich context — function names, imports, class names, complexity
6. **Calls** an LLM (Llama 3.3 70B via Groq) with the structured context
7. **Posts** inline review comments directly on the PR with severity ratings

### Example Output

```
🔴 ERROR   | auth.py:4  | Insecure password hashing (MD5)
🔴 ERROR   | auth.py:7  | Division by zero — no guard clause
🟡 WARNING | auth.py:3  | Missing docstring
🟡 WARNING | auth.py:6  | Function name does not match its purpose
```

---

## 🏗️ Architecture

```
GitHub PR Opened
      │
      ▼
GitHub Webhook POST
      │
      ▼
FastAPI Server (webhook.py)
      │
      ├── HMAC Signature Verification
      │
      ▼
Background Task Pipeline
      │
      ├── 1. Fetch raw diff (GitHub API)
      ├── 2. Parse diff → DiffHunk objects (diff_parser.py)
      ├── 3. Fetch full file content (GitHub API)
      ├── 4. AST analysis → CodeContext (context_builder.py)
      ├── 5. Build LLM prompt
      ├── 6. Call Groq API (review_engine.py)
      └── 7. Post review comments (github_client.py)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI + Uvicorn |
| **LLM** | Llama 3.3 70B via Groq API |
| **Code Analysis** | Python AST module |
| **GitHub Integration** | GitHub Webhooks + REST API |
| **Webhook Tunnel** | ngrok |
| **Config Management** | Pydantic Settings |
| **HTTP Client** | httpx (async) |

---

## 📁 Project Structure

```
ai-code-reviewer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py          # API router
│   │   │   └── webhook.py         # GitHub webhook handler + HMAC verification
│   │   ├── core/
│   │   │   ├── diff_parser.py     # Parses unified git diffs → structured objects
│   │   │   ├── context_builder.py # AST analysis + GitHub file fetching
│   │   │   ├── review_engine.py   # LLM prompt building + Groq API calls
│   │   │   └── github_client.py   # GitHub API — fetch diffs, post reviews
│   │   ├── services/
│   │   │   └── review_service.py  # Orchestrates the full pipeline
│   │   ├── config.py              # Pydantic settings — reads from .env
│   │   └── main.py                # FastAPI app entry point
│   ├── ml/
│   │   ├── dataset_builder.py     # Scrapes GitHub PRs for fine-tuning data
│   │   ├── train.py               # QLoRA fine-tuning with PEFT
│   │   └── evaluate.py            # LLM-as-judge evaluation harness
│   ├── tests/
│   │   ├── test_diff_parser.py
│   │   └── test_review_engine.py
│   └── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A GitHub account
- A [Groq API key](https://console.groq.com) (free)
- [ngrok](https://ngrok.com) for local webhook tunneling

### 1. Clone and Install

```bash
git clone https://github.com/HamzzaFareed/ai-code-reviewer.git
cd ai-code-reviewer/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Fill in your `.env`:

```env
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_TOKEN=your_github_personal_access_token
GROQ_API_KEY=your_groq_api_key
APP_ENV=development
APP_PORT=8000
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Expose via ngrok

```bash
ngrok http 8000
```

### 5. Configure GitHub Webhook

In your repo → Settings → Webhooks → Add webhook:
- **Payload URL:** `https://your-ngrok-url.ngrok-free.app/api/v1/webhook/github`
- **Content type:** `application/json`
- **Secret:** same as `GITHUB_WEBHOOK_SECRET` in `.env`
- **Events:** Pull requests only

### 6. Open a PR and Watch It Work!

---

## 🧠 Key Engineering Decisions

### Why AST instead of regex for code analysis?
Python's `ast` module gives us a proper parse tree of the code — we can find exactly which function and class a changed line belongs to, extract all imports, and calculate cyclomatic complexity. Regex-based approaches miss nested structures and break on edge cases.

### Why background tasks instead of sync processing?
GitHub expects a webhook response within 10 seconds or it retries. LLM calls can take 20-60 seconds. FastAPI's `BackgroundTasks` lets us return 200 immediately and process in the background.

### Why structured JSON output from the LLM?
The system prompt forces the LLM to return a strict JSON schema with `file_path`, `line_number`, `severity`, and `suggestion` fields. This makes parsing reliable and enables us to post precise inline comments at exact line numbers.

---

## 📊 What the LLM Catches

- 🔴 **Security issues** — hardcoded secrets, insecure hashing (MD5/SHA1), SQL injection patterns
- 🔴 **Bugs** — division by zero, missing null checks, off-by-one errors
- 🟡 **Performance** — N+1 queries, unnecessary loops, missing indexes
- 🟡 **Bad practices** — missing docstrings, functions doing too much, poor naming
- 🔵 **Style** — inconsistent formatting, unused imports

---

## 🔮 Roadmap

- [ ] Fine-tune Qwen2.5-Coder on real PR review data using QLoRA
- [ ] LLM-as-judge evaluation harness to score review quality
- [ ] Next.js dashboard to visualize review history
- [ ] Redis + Celery task queue for production scale
- [ ] Docker + Railway deployment

---

## 👨‍💻 Author

**Hamza Fareed** — BS AI Student  
Built as a portfolio project to demonstrate LLM engineering, GitHub API integration, and production-grade Python backend development.

---

*If this project helped you, give it a ⭐*