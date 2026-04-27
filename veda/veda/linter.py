from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LintIssue:
    code: str
    message: str
    line: int
    column: int = 1


def lint_source(source: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    lines = source.splitlines()

    for i, line in enumerate(lines, start=1):
        if "\t" in line:
            issues.append(LintIssue("L001", "Tab character found; use spaces.", i, line.index("\t") + 1))
        if line.rstrip("\n\r") != line.rstrip("\n\r ").rstrip("\n\r"):
            # trailing spaces
            stripped = line.rstrip("\n\r")
            if stripped.endswith(" "):
                issues.append(LintIssue("L002", "Trailing whitespace.", i, len(stripped)))
        # indentation multiple of 4 (ignore blank)
        if line.strip():
            leading = len(line) - len(line.lstrip(" "))
            if leading % 4 != 0:
                issues.append(LintIssue("L003", "Indentation should use multiples of 4 spaces.", i, 1))

    if source and not source.endswith("\n"):
        issues.append(LintIssue("L004", "File should end with a newline.", len(lines) or 1, 1))

    return issues


def fix_source(source: str) -> str:
    # Minimal auto-fix: trim trailing whitespace and ensure final newline.
    lines = [ln.rstrip(" \t") for ln in source.splitlines()]
    fixed = "\n".join(lines) + "\n"
    return fixed

