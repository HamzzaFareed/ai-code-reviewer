import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiffLine:
    """Represents a single line in a diff."""
    line_number: int
    content: str
    change_type: str   # "added", "removed", "context"


@dataclass
class DiffHunk:
    """
    A hunk is one continuous block of changes in a file.
    A single file can have multiple hunks if changes are spread out.
    """
    file_path: str
    language: str
    start_line: int
    lines: list[DiffLine] = field(default_factory=list)

    @property
    def added_lines(self) -> list[DiffLine]:
        return [l for l in self.lines if l.change_type == "added"]

    @property
    def removed_lines(self) -> list[DiffLine]:
        return [l for l in self.lines if l.change_type == "removed"]

    @property
    def changed_line_numbers(self) -> list[int]:
        return [l.line_number for l in self.added_lines]

    def to_context_string(self) -> str:
        """Formats the hunk into a clean string for the LLM prompt."""
        lines_text = []
        for line in self.lines:
            prefix = {
                "added": "+",
                "removed": "-",
                "context": " "
            }[line.change_type]
            lines_text.append(f"{prefix} {line.line_number:4d} | {line.content}")
        return "\n".join(lines_text)


@dataclass
class ParsedDiff:
    """The full parsed diff for a PR — contains all hunks across all files."""
    hunks: list[DiffHunk] = field(default_factory=list)

    @property
    def changed_files(self) -> list[str]:
        return list({h.file_path for h in self.hunks})

    @property
    def total_additions(self) -> int:
        return sum(len(h.added_lines) for h in self.hunks)

    @property
    def total_deletions(self) -> int:
        return sum(len(h.removed_lines) for h in self.hunks)

    def get_hunks_for_file(self, file_path: str) -> list[DiffHunk]:
        return [h for h in self.hunks if h.file_path == file_path]


# maps file extensions to language names for the LLM prompt
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".md": "markdown",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".sh": "bash",
}


def detect_language(file_path: str) -> str:
    """Detects language from file extension."""
    for ext, lang in EXTENSION_TO_LANGUAGE.items():
        if file_path.endswith(ext):
            return lang
    return "unknown"


def parse_diff(raw_diff: str) -> ParsedDiff:
    """
    Parses a raw unified git diff string into structured DiffHunk objects.

    A unified diff looks like:
    diff --git a/file.py b/file.py
    --- a/file.py
    +++ b/file.py
    @@ -10,6 +10,8 @@        ← hunk header: start line info
     def foo():              ← context line (space prefix)
    -    return 1            ← removed line (- prefix)
    +    return 2            ← added line (+ prefix)
    """
    parsed = ParsedDiff()

    current_file = None
    current_language = "unknown"
    current_hunk = None
    current_line_number = 0

    for line in raw_diff.splitlines():

        # new file section
        if line.startswith("diff --git"):
            current_hunk = None

        # extract file path from +++ b/filepath
        elif line.startswith("+++ b/"):
            current_file = line[6:]   # strip "+++ b/"
            current_language = detect_language(current_file)

        # hunk header: @@ -old_start,old_count +new_start,new_count @@
        elif line.startswith("@@") and current_file:
            match = re.search(r"\+(\d+)", line)
            if match:
                current_line_number = int(match.group(1))
                current_hunk = DiffHunk(
                    file_path=current_file,
                    language=current_language,
                    start_line=current_line_number,
                )
                parsed.hunks.append(current_hunk)

        # diff content lines
        elif current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.lines.append(DiffLine(
                    line_number=current_line_number,
                    content=line[1:],
                    change_type="added"
                ))
                current_line_number += 1

            elif line.startswith("-") and not line.startswith("---"):
                current_hunk.lines.append(DiffLine(
                    line_number=current_line_number,
                    content=line[1:],
                    change_type="removed"
                ))
                # removed lines don't increment the new file's line number

            elif line.startswith(" "):
                current_hunk.lines.append(DiffLine(
                    line_number=current_line_number,
                    content=line[1:],
                    change_type="context"
                ))
                current_line_number += 1

    return parsed