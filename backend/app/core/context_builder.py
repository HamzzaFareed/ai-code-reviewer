import ast
import re
import httpx
from typing import Optional
from dataclasses import dataclass, field
from app.core.diff_parser import DiffHunk, ParsedDiff, parse_diff
from app.config import get_settings

settings = get_settings()


@dataclass
class CodeContext:
    """
    Rich context for a single hunk — everything the LLM
    needs to write a smart, accurate review comment.
    """
    hunk: DiffHunk
    function_name: Optional[str]        # which function was changed
    class_name: Optional[str]           # which class it belongs to
    imports: list[str]                  # all imports in the file
    related_functions: list[str]        # other functions in same file
    complexity_score: int               # rough cyclomatic complexity
    has_tests: bool                     # does a test file exist for this?

    def to_prompt_section(self) -> str:
        """
        Formats everything into a clean section for the LLM prompt.
        This is what the model actually sees.
        """
        parts = []

        parts.append(f"### File: `{self.hunk.file_path}` ({self.hunk.language})")

        if self.class_name:
            parts.append(f"**Class:** `{self.class_name}`")
        if self.function_name:
            parts.append(f"**Function:** `{self.function_name}`")
        if self.imports:
            parts.append(f"**Imports:** {', '.join(self.imports[:8])}")  # cap at 8
        if self.related_functions:
            parts.append(f"**Other functions in file:** {', '.join(self.related_functions[:5])}")

        parts.append(f"**Complexity score:** {self.complexity_score}")
        parts.append(f"**Has tests:** {'yes' if self.has_tests else 'no'}")
        parts.append(f"\n**Changed code:**\n```{self.hunk.language}\n{self.hunk.to_context_string()}\n```")

        return "\n".join(parts)



class ContextBuilder:
    """
    Builds rich context for each diff hunk by:
    1. Fetching the full file from GitHub
    2. Running Python AST analysis (for .py files)
    3. Extracting imports, function names, class names
    4. Estimating code complexity
    """

    def __init__(self):
        self.github_token = settings.github_token
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3.raw",
        }

    async def fetch_file_content(self, repo: str, file_path: str, ref: str) -> Optional[str]:
        """Fetches the full file content from GitHub API."""
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={ref}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                if response.status_code == 200:
                    return response.text
                return None
            except httpx.TimeoutException:
                print(f"Timeout fetching {file_path}")
                return None

    def extract_python_context(self, source_code: str, changed_lines: list[int]) -> dict:
        """
        Uses Python's built-in AST module to analyze source code.
        AST = Abstract Syntax Tree — a tree representation of the code structure.
        No regex hacks, this is the proper way to analyze Python code.
        """
        context = {
            "imports": [],
            "function_name": None,
            "class_name": None,
            "related_functions": [],
            "complexity_score": 1,
        }

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return context  # unparseable, return empty context

        # extract all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    context["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    context["imports"].append(f"{module}.{alias.name}")

        # find which function/class the changed lines belong to
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_start = node.lineno
                func_end = node.end_lineno or func_start

                # check if any changed line falls inside this function
                if any(func_start <= line <= func_end for line in changed_lines):
                    context["function_name"] = node.name

                    # check if this function is inside a class
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            for child in ast.walk(parent):
                                if child is node:
                                    context["class_name"] = parent.name

                context["related_functions"].append(node.name)

            # complexity: count branches (if, for, while, try, with)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try,
                                  ast.ExceptHandler, ast.With, ast.BoolOp)):
                context["complexity_score"] += 1

        # remove the changed function from related_functions list
        if context["function_name"] in context["related_functions"]:
            context["related_functions"].remove(context["function_name"])

        return context

    def extract_generic_context(self, source_code: str, language: str) -> dict:
        """
        For non-Python files — simple regex-based extraction.
        Not as powerful as AST but still useful for JS/TS/etc.
        """
        import re
        context = {
            "imports": [],
            "function_name": None,
            "class_name": None,
            "related_functions": [],
            "complexity_score": 1,
        }

        # JS/TS imports
        if language in ("javascript", "typescript"):
            imports = re.findall(r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]', source_code)
            context["imports"] = imports

            # function names
            funcs = re.findall(
                r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()', source_code
            )
            context["related_functions"] = [f[0] or f[1] for f in funcs]

        # complexity: count branches
        branch_keywords = ["if ", "else ", "for ", "while ", "catch ", "switch "]
        for kw in branch_keywords:
            context["complexity_score"] += source_code.count(kw)

        return context

    async def build_context(
        self,
        hunk: DiffHunk,
        repo: str,
        pr_head_sha: str,
        all_files: list[str]
    ) -> CodeContext:
        """
        Main method — builds full CodeContext for a single hunk.
        """
        # fetch the full file from GitHub
        source_code = await self.fetch_file_content(repo, hunk.file_path, pr_head_sha)

        changed_lines = hunk.changed_line_numbers

        # run language-appropriate analysis
        if hunk.language == "python" and source_code:
            raw_context = self.extract_python_context(source_code, changed_lines)
        elif source_code:
            raw_context = self.extract_generic_context(source_code, hunk.language)
        else:
            raw_context = {
                "imports": [], "function_name": None,
                "class_name": None, "related_functions": [],
                "complexity_score": 1
            }

        # check if a test file exists for this file
        base_name = hunk.file_path.replace(".py", "").replace("/", "_")
        has_tests = any(
            "test" in f.lower() and base_name.split("_")[-1] in f
            for f in all_files
        )

        return CodeContext(
            hunk=hunk,
            function_name=raw_context["function_name"],
            class_name=raw_context["class_name"],
            imports=raw_context["imports"],
            related_functions=raw_context["related_functions"],
            complexity_score=raw_context["complexity_score"],
            has_tests=has_tests,
        )

    async def build_all_contexts(
        self,
        parsed_diff: ParsedDiff,
        repo: str,
        pr_head_sha: str,
        all_files: list[str]
    ) -> list[CodeContext]:
        """Builds context for every hunk in the diff."""
        contexts = []
        for hunk in parsed_diff.hunks:
            # skip files that are unlikely to need review
            if hunk.language in ("unknown", "markdown", "json", "yaml"):
                continue
            ctx = await self.build_context(hunk, repo, pr_head_sha, all_files)
            contexts.append(ctx)
        return contexts