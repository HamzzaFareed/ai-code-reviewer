import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.config import get_settings
from app.services.review_service import run_review

router = APIRouter()
settings = get_settings()


def verify_github_signature(payload: bytes, signature: str) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        key=settings.github_webhook_secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    actual = signature.split("sha256=")[1]
    return hmac.compare_digest(expected, actual)


async def process_pull_request(pr_data: dict):
    pr_number = pr_data["pull_request"]["number"]
    repo = pr_data["repository"]["full_name"]
    print(f"[PR #{pr_number}] Webhook received for {repo}")
    await run_review(pr_data)


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")

    if not verify_github_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if event_type == "ping":
        print("GitHub ping received — webhook connected successfully!")
        return {"message": "pong"}

    if event_type != "pull_request":
        return {"message": f"Event '{event_type}' ignored"}

    action = data.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return {"message": f"Action '{action}' ignored"}

    background_tasks.add_task(process_pull_request, data)

    return {
        "message": "PR received, review queued",
        "pr": data["pull_request"]["number"],
        "repo": data["repository"]["full_name"]
    }


@router.get("/github")
async def webhook_health():
    return {"status": "webhook endpoint live"}