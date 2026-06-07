---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A GitHub account
- A Groq API key — free at console.groq.com
- ngrok for local webhook tunneling

---

### Backend Setup

**1. Clone the repo**

```bash
git clone https://github.com/HamzzaFareed/ai-code-reviewer.git
cd ai-code-reviewer/backend
```

**2. Create virtual environment**

```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment**

```bash
cp .env.example .env
```

Fill in your `.env`:

```env
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_TOKEN=your_github_personal_access_token
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
MODEL_NAME=Qwen/Qwen2.5-Coder-7B-Instruct
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
APP_PORT=8000
```

**5. Run the backend**

```bash
uvicorn app.main:app --reload --port 8000
```

Server runs at http://127.0.0.1:8000
Swagger docs at http://127.0.0.1:8000/docs

---

### Frontend Setup

Open a new terminal:

```bash
cd ai-code-reviewer/frontend
npm install
npm run dev
```

Dashboard runs at http://localhost:3000

---

### Webhook Setup

**1. Expose your local server**

Open a third terminal:

```bash
ngrok http 8000
```

Copy the forwarding URL — looks like `https://xxxx.ngrok-free.app`

**2. Add webhook to your GitHub repo**

Go to your repo on GitHub:
- Settings → Webhooks → Add webhook
- Payload URL: `https://xxxx.ngrok-free.app/api/v1/webhook/github`
- Content type: `application/json`
- Secret: same value as `GITHUB_WEBHOOK_SECRET` in your `.env`
- Events: select Pull requests only
- Click Add webhook

**3. Test it**

Open a Pull Request in your repo with some Python code. Watch the backend terminal — you will see the full pipeline run and AI comments appear on your PR within seconds.

---

## Running the Full Stack

You need 3 terminals running simultaneously:

| Terminal | Command | Location |
|----------|---------|----------|
| 1 — Backend | `uvicorn app.main:app --reload --port 8000` | `backend/` |
| 2 — Frontend | `npm run dev` | `frontend/` |
| 3 — ngrok | `ngrok http 8000` | anywhere |

Note: ngrok gives a new URL every restart on the free plan. Update your GitHub webhook URL whenever you restart ngrok.

---

## Key Engineering Decisions

**Why AST instead of regex for code analysis?**
Python's `ast` module gives us a proper parse tree of the code. We can find exactly which function and class a changed line belongs to, extract all imports, and calculate cyclomatic complexity. Regex-based approaches miss nested structures and break on edge cases.

**Why background tasks instead of sync processing?**
GitHub expects a webhook response within 10 seconds or it retries. LLM calls can take 20-60 seconds. FastAPI's `BackgroundTasks` lets us return 200 immediately and process in the background.

**Why structured JSON output from the LLM?**
The system prompt forces the LLM to return a strict JSON schema with `file_path`, `line_number`, `severity`, and `suggestion` fields. This makes parsing reliable and enables precise inline comments at exact line numbers.

---

## What the LLM Catches

- Security issues — hardcoded secrets, insecure hashing (MD5/SHA1), SQL injection
- Bugs — division by zero, missing null checks, off-by-one errors
- Performance — N+1 queries, unnecessary loops, missing indexes
- Bad practices — missing docstrings, functions doing too much, poor naming
- Style — inconsistent formatting, unused imports

---

## Roadmap

- [ ] Fine-tune Qwen2.5-Coder on real PR review data using QLoRA
- [ ] LLM-as-judge evaluation harness to score review quality
- [ ] Redis + Celery task queue for production scale
- [ ] Docker + Railway deployment

---

## Author

**Hamza Fareed** — BS AI Student
Built as a portfolio project to demonstrate LLM engineering, GitHub API integration, and production-grade Python backend development.

---

*If this project helped you, give it a star*