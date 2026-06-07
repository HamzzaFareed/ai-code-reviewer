import httpx
from typing import Optional
from app.core.review_engine import ReviewResult, ReviewComment
from app.config import get_settings

settings = get_settings()

GITHUB_API = "https://api.github.com"


class GitHubClient:

    def __init__(self):
        self.token = settings.github_token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pr_details(self, repo: str, pr_number: int) -> dict:
        url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=15.0)
            response.raise_for_status()
            return response.text

    async def get_pr_files(self, repo: str, pr_number: int) -> list[str]:
        url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            files = response.json()
            return [f["filename"] for f in files]

    async def create_review(
        self,
        repo: str,
        pr_number: int,
        commit_sha: str,
        review_result: ReviewResult,
    ) -> dict:
        url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews"

        inline_comments = []
        for comment in review_result.comments:
            emoji_map = {"error": "🔴", "warning": "🟡", "nit": "🔵"}
            emoji = emoji_map.get(comment.severity, "⚪")

            body = f"""{emoji} **{comment.severity.upper()}** — {comment.title}

{comment.body}

**Suggestion:** {comment.suggestion}
"""
            inline_comments.append({
                "path": comment.file_path,
                "position": comment.line_number,
                "body": body
            })

        event = "COMMENT"

        payload = {
            "commit_id": commit_sha,
            "body": review_result.to_github_body(),
            "event": event,
            "comments": inline_comments,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=15.0
            )
            if response.status_code not in (200, 201):
                print(f"GitHub API error: {response.status_code} — {response.text}")
                response.raise_for_status()
            return response.json()

    async def post_comment(self, repo: str, pr_number: int, body: str) -> dict:
        url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json={"body": body},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def set_commit_status(
        self,
        repo: str,
        commit_sha: str,
        state: str,
        description: str,
    ) -> dict:
        url = f"{GITHUB_API}/repos/{repo}/statuses/{commit_sha}"
        payload = {
            "state": state,
            "description": description,
            "context": "ai-code-reviewer",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()