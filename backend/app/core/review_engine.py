import json
import httpx
from dataclasses import dataclass, field


@dataclass
class ReviewComment:
    file_path: str
    line_number: int
    severity: str
    category: str
    title: str
    body: str
    suggestion: str


@dataclass
class ReviewResult:
    pr_number: int
    repo: str
    comments: list[ReviewComment] = field(default_factory=list)
    summary: str = ""
    total_issues: int = 0
    has_blocking_issues: bool = False

    def to_github_body(self) -> str:
        emoji_map = {"error": "🔴", "warning": "🟡", "nit": "🔵"}
        lines = [
            "## 🤖 AI Code Review",
            f"> {self.summary}",
            "",
            f"**{self.total_issues} issue(s) found** across {len(set(c.file_path for c in self.comments))} file(s)",
            "",
            "| Severity | File | Issue |",
            "|----------|------|-------|",
        ]
        for c in self.comments:
            emoji = emoji_map.get(c.severity, "⚪")
            lines.append(f"| {emoji} {c.severity} | `{c.file_path}:{c.line_number}` | {c.title} |")
        lines += ["", "---", "*Powered by AI Code Review Agent*"]
        return "\n".join(lines)


SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices, security vulnerabilities, performance optimization, and clean code principles.

Your job is to review code changes (diffs) and provide actionable, specific feedback.

You must respond with ONLY a valid JSON object — no explanation, no markdown, no preamble.

JSON format:
{
  "summary": "One sentence summary of the overall code quality",
  "comments": [
    {
      "file_path": "path/to/file.py",
      "line_number": 42,
      "severity": "error|warning|nit",
      "category": "bug|security|performance|style|logic",
      "title": "Short title of the issue",
      "body": "Detailed explanation of why this is a problem",
      "suggestion": "Concrete code suggestion to fix this"
    }
  ]
}

Severity guide:
- error: bugs, security issues, will break in production
- warning: bad practices, potential bugs, performance issues
- nit: style issues, minor improvements, optional

Rules:
- Only comment on the changed lines (lines marked with +)
- Be specific — reference actual variable names and line numbers
- Provide a concrete suggestion for every comment
- Maximum 10 comments per review — prioritize the most important issues
- If the code is good, return an empty comments array with a positive summary
"""


def build_review_prompt(contexts) -> str:
    parts = ["Please review the following code changes:\n"]
    for i, ctx in enumerate(contexts, 1):
        parts.append(f"## Change {i}")
        parts.append(ctx.to_prompt_section())
        parts.append("")
    parts.append("\nRespond with ONLY the JSON object.")
    return "\n".join(parts)


def parse_llm_response(response_text: str) -> tuple[str, list[dict]]:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        data = json.loads(text)
        return data.get("summary", ""), data.get("comments", [])
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}")
        print(f"Raw response: {response_text[:500]}")
        return "Could not parse review", []


class ReviewEngine:

    def __init__(self):
        from app.config import get_settings
        s = get_settings()
        self.groq_api_key = s.groq_api_key
        self.model_name = "llama-3.1-8b-instant"
        print(f"[DEBUG] Groq key loaded: {self.groq_api_key[:10]}...")
        print(f"[DEBUG] Model: {self.model_name}")

    async def call_llm(self, prompt: str) -> str:
        from app.config import get_settings
        s = get_settings()

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {s.groq_api_key}"},
                json=payload
            )
            if response.status_code != 200:
                raise Exception(f"Groq API error {response.status_code}: {response.text}")
            result = response.json()
            return result["choices"][0]["message"]["content"]

    async def review(self, contexts, pr_number: int, repo: str) -> ReviewResult:
        if not contexts:
            return ReviewResult(
                pr_number=pr_number,
                repo=repo,
                summary="No reviewable code changes found.",
            )

        prompt = build_review_prompt(contexts)
        print(f"[PR #{pr_number}] Calling LLM with {len(contexts)} context(s)...")

        raw_response = await self.call_llm(prompt)
        summary, raw_comments = parse_llm_response(raw_response)

        comments = []
        for c in raw_comments:
            try:
                comments.append(ReviewComment(
                    file_path=c.get("file_path", "unknown"),
                    line_number=int(c.get("line_number", 1)),
                    severity=c.get("severity", "nit"),
                    category=c.get("category", "style"),
                    title=c.get("title", ""),
                    body=c.get("body", ""),
                    suggestion=c.get("suggestion", ""),
                ))
            except (ValueError, KeyError) as e:
                print(f"Skipping malformed comment: {e}")

        result = ReviewResult(
            pr_number=pr_number,
            repo=repo,
            comments=comments,
            summary=summary,
            total_issues=len(comments),
            has_blocking_issues=any(c.severity == "error" for c in comments),
        )

        print(f"[PR #{pr_number}] Review done — {len(comments)} issue(s) found")
        return result