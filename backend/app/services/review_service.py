from app.core.diff_parser import parse_diff
from app.core.context_builder import ContextBuilder
from app.core.review_engine import ReviewEngine
from app.core.github_client import GitHubClient


async def run_review(pr_data: dict):
    repo = pr_data["repository"]["full_name"]
    pr_number = pr_data["pull_request"]["number"]
    commit_sha = pr_data["pull_request"]["head"]["sha"]

    github = GitHubClient()
    context_builder = ContextBuilder()
    review_engine = ReviewEngine()

    print(f"[PR #{pr_number}] Starting review pipeline for {repo}")

    try:
        # fetch the raw diff
        print(f"[PR #{pr_number}] Fetching diff...")
        raw_diff = await github.get_pr_diff(repo, pr_number)

        # parse the diff
        parsed_diff = parse_diff(raw_diff)
        print(f"[PR #{pr_number}] Parsed {len(parsed_diff.hunks)} hunk(s) across {len(parsed_diff.changed_files)} file(s)")

        # get all files in PR
        all_files = await github.get_pr_files(repo, pr_number)

        # build context
        print(f"[PR #{pr_number}] Building context...")
        contexts = await context_builder.build_all_contexts(
            parsed_diff, repo, commit_sha, all_files
        )
        print(f"[PR #{pr_number}] Built {len(contexts)} context(s)")

        # call LLM
        review_result = await review_engine.review(contexts, pr_number, repo)

        # post to GitHub
        if review_result.comments:
            print(f"[PR #{pr_number}] Posting {len(review_result.comments)} comment(s)...")
            await github.create_review(repo, pr_number, commit_sha, review_result)
        else:
            await github.post_comment(repo, pr_number, review_result.to_github_body())

        print(f"[PR #{pr_number}] Review complete!")

    except Exception as e:
        print(f"[PR #{pr_number}] Pipeline error: {e}")
        raise