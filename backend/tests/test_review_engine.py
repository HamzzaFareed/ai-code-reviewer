import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.review_engine import parse_llm_response, build_review_prompt, ReviewResult, ReviewComment

def test_parse_llm_response():
    # simulate what the LLM returns
    fake_response = '''```json
{
  "summary": "Found a critical security issue in password hashing",
  "comments": [
    {
      "file_path": "auth.py",
      "line_number": 9,
      "severity": "error",
      "category": "security",
      "title": "MD5 is not safe for password hashing",
      "body": "MD5 is cryptographically broken. Passwords hashed with MD5 can be cracked trivially using rainbow tables.",
      "suggestion": "Use bcrypt or argon2 instead: pip install bcrypt, then bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
    }
  ]
}
```'''

    summary, comments = parse_llm_response(fake_response)

    print(f"\n summary: {summary}")
    print(f" comments found: {len(comments)}")
    print(f" severity: {comments[0]['severity']}")
    print(f" category: {comments[0]['category']}")

    assert "security" in summary.lower() or len(comments) > 0
    assert comments[0]["severity"] == "error"
    assert comments[0]["category"] == "security"
    print("\n parse test passed!")

def test_review_result_formatting():
    result = ReviewResult(
        pr_number=42,
        repo="testuser/testrepo",
        summary="Found 1 critical security issue",
        total_issues=1,
        has_blocking_issues=True,
        comments=[
            ReviewComment(
                file_path="auth.py",
                line_number=9,
                severity="error",
                category="security",
                title="MD5 is not safe for password hashing",
                body="MD5 is broken.",
                suggestion="Use bcrypt instead."
            )
        ]
    )

    github_body = result.to_github_body()
    print(f"\n github comment preview:\n{github_body}")

    assert "🔴" in github_body
    assert "auth.py" in github_body
    assert "AI Code Review" in github_body
    print("\n formatting test passed!")

if __name__ == "__main__":
    test_parse_llm_response()
    test_review_result_formatting()
