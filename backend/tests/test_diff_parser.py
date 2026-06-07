import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.diff_parser import parse_diff

SAMPLE_DIFF = """diff --git a/calculator.py b/calculator.py
--- a/calculator.py
+++ b/calculator.py
@@ -1,7 +1,10 @@
 def add(a, b):
-    return a - b
+    return a + b
 
 def divide(a, b):
-    return a / b
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
+    return a / b
"""

def test_parse_diff():
    result = parse_diff(SAMPLE_DIFF)

    print(f"\n files changed: {result.changed_files}")
    print(f" total additions: {result.total_additions}")
    print(f" total deletions: {result.total_deletions}")
    print(f" hunks: {len(result.hunks)}")
    print(f"\n hunk context:\n{result.hunks[0].to_context_string()}")

    assert "calculator.py" in result.changed_files
    assert result.total_additions == 4
    assert result.total_deletions == 2
    print("\n all assertions passed!")

if __name__ == "__main__":
    test_parse_diff()
from app.core.context_builder import ContextBuilder

SAMPLE_PYTHON_CODE = """
import os
import hashlib

class UserAuth:
    def __init__(self, secret):
        self.secret = secret

    def hash_password(self, password):
        return hashlib.md5(password.encode()).hexdigest()

    def verify(self, password, hashed):
        return self.hash_password(password) == hashed

def create_user(username, password):
    if not username:
        raise ValueError("Username required")
    return {"username": username}
"""

def test_ast_context():
    builder = ContextBuilder()

    # simulate changed lines 9 and 10 (inside hash_password)
    context = builder.extract_python_context(SAMPLE_PYTHON_CODE, changed_lines=[9, 10])

    print(f"\n function found: {context['function_name']}")
    print(f" class found: {context['class_name']}")
    print(f" imports: {context['imports']}")
    print(f" related functions: {context['related_functions']}")
    print(f" complexity score: {context['complexity_score']}")

    assert context["function_name"] == "hash_password"
    assert context["class_name"] == "UserAuth"
    assert "hashlib" in context["imports"]
    print("\n AST test passed!")

if __name__ == "__main__":
    test_parse_diff()
    test_ast_context()