# file_helpers.py - utilities for loading files and presenting DSPy results
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import dspy


# Directories that should never be traversed when collecting source files.
ALWAYS_IGNORED_DIRS: set[str] = {
    "__pycache__",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    ".vscode",
    ".idea",
    "venv",
}

# Individual files or suffixes that should never be analyzed.
ALWAYS_IGNORED_FILES: set[str] = {".DS_Store"}
ALWAYS_IGNORED_SUFFIXES: set[str] = {".pyc", ".pyo"}


def _normalize_relative_parts(value: Path | str) -> tuple[str, ...]:
    """Return normalized path segments for relative comparisons."""

    text = str(value).replace("\\", "/").strip()
    if not text:
        return ()
    text = text.strip("/")
    if not text or text in {"", "."}:
        return ()

    parts: list[str] = []
    for segment in text.split("/"):
        if not segment or segment == ".":
            continue
        if segment == "..":
            if parts:
                parts.pop()
            continue
        parts.append(segment)
    return tuple(parts)


def _matches_excluded_parts(
    parts: tuple[str, ...],
    excluded_parts: set[tuple[str, ...]],
) -> bool:
    for excluded in excluded_parts:
        if len(parts) < len(excluded):
            continue
        if parts[: len(excluded)] == excluded:
            return True
    return False


def _normalize_excluded_dirs(exclude_dirs: Iterable[str] | None) -> set[tuple[str, ...]]:
    """Normalize raw exclude strings into comparable path segments."""

    normalized: set[tuple[str, ...]] = set()
    if not exclude_dirs:
        return normalized

    for raw in exclude_dirs:
        cleaned = raw.strip()
        if not cleaned:
            continue
        parts = _normalize_relative_parts(cleaned)
        if parts:
            normalized.add(parts)
    return normalized


def _relative_path_is_excluded(
    relative_path: Path,
    excluded_parts: set[tuple[str, ...]],
) -> bool:
    if not excluded_parts:
        return False
    parts = _normalize_relative_parts(relative_path)
    if not parts:
        return False
    return _matches_excluded_parts(parts, excluded_parts)


def resolve_file_path(raw_path: str) -> Path:
    """Expand user shortcuts and validate that the target file exists."""

    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Expected a file path but received: {path}")
    return path


def _pattern_targets_hidden(pattern: str) -> bool:
    pattern = pattern.strip()
    if not pattern:
        return False
    normalized = pattern[2:] if pattern.startswith("./") else pattern
    return normalized.startswith(".") or "/." in normalized


def _should_skip_dir(name: str, *, ignore_hidden: bool) -> bool:
    if name in ALWAYS_IGNORED_DIRS:
        return True
    if ignore_hidden and name.startswith("."):
        return True
    return False


def _should_skip_file(name: str, *, ignore_hidden: bool) -> bool:
    if name in ALWAYS_IGNORED_FILES:
        return True
    if any(name.endswith(suffix) for suffix in ALWAYS_IGNORED_SUFFIXES):
        return True
    if ignore_hidden and name.startswith("."):
        return True
    return False


def _should_skip_relative_path(
    relative_path: Path,
    *,
    ignore_hidden: bool,
    excluded_parts: set[tuple[str, ...]] | None = None,
) -> bool:
    parts = _normalize_relative_parts(relative_path)
    if not parts:
        return False

    if excluded_parts and _matches_excluded_parts(parts, excluded_parts):
        return True

    # Check intermediate directories for ignore rules.
    for segment in parts[:-1]:
        if segment in ALWAYS_IGNORED_DIRS:
            return True
        if ignore_hidden and segment.startswith("."):
            return True

    return _should_skip_file(parts[-1], ignore_hidden=ignore_hidden)


def collect_source_paths(
    raw_path: str,
    *,
    recursive: bool = True,
    include_globs: Iterable[str] | None = None,
    exclude_dirs: Iterable[str] | None = None,
) -> list[Path]:
    """Resolve a single file or directory into an ordered list of file paths."""

    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Target not found: {path}")

    if path.is_file():
        return [path]

    if not path.is_dir():
        raise IsADirectoryError(f"Expected file or directory path but received: {path}")

    candidates: set[Path] = set()
    patterns = list(include_globs) if include_globs else None
    allow_hidden = any(_pattern_targets_hidden(pattern) for pattern in patterns) if patterns else False
    ignore_hidden = not allow_hidden
    excluded_parts = _normalize_excluded_dirs(exclude_dirs)

    if patterns:
        for pattern in patterns:
            for candidate in path.glob(pattern):
                if not candidate.is_file():
                    continue

                relative_candidate = candidate.relative_to(path)
                if _should_skip_relative_path(
                    relative_candidate,
                    ignore_hidden=ignore_hidden,
                    excluded_parts=excluded_parts,
                ):
                    continue

                candidates.add(candidate.resolve())
    else:
        for root_dir, dirnames, filenames in os.walk(path):
            root_path = Path(root_dir)
            relative_root = Path(".") if root_path == path else root_path.relative_to(path)

            if not recursive and root_path != path:
                dirnames[:] = []
                continue

            if _relative_path_is_excluded(relative_root, excluded_parts):
                dirnames[:] = []
                continue

            dirnames[:] = sorted(
                name
                for name in dirnames
                if not _should_skip_dir(name, ignore_hidden=ignore_hidden)
                and not _relative_path_is_excluded(relative_root / name, excluded_parts)
            )

            for filename in filenames:
                candidate = root_path / filename
                relative_candidate = candidate.relative_to(path)

                if _should_skip_relative_path(
                    relative_candidate,
                    ignore_hidden=ignore_hidden,
                    excluded_parts=excluded_parts,
                ):
                    continue

                candidates.add(candidate.resolve())

    return sorted(candidates)


def _strip_front_matter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end_idx = text.find("\n---", 3)
    if end_idx == -1:
        return text
    return text[end_idx + 4 :]


def _trim_to_first_heading(text: str) -> str:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            return "\n".join(lines[idx:])
    return text


def read_file_content(path: Path) -> str:
    """Read file contents using utf-8 and fall back to latin-1 if needed."""

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="latin-1")

    cleaned = _strip_front_matter(raw)
    cleaned = _trim_to_first_heading(cleaned)
    return cleaned


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def _teaching_output(result: dspy.Prediction) -> str:
    try:
        report = result.report.report_markdown  # type: ignore[attr-defined]
    except AttributeError:
        report = "# Teaching Brief\n\nThe DSPy pipeline did not produce a report."
    return _ensure_trailing_newline(report)


def _refactor_output(result: dspy.Prediction) -> str:
    template = getattr(result, "template_markdown", None)
    if not template:
        template = getattr(getattr(result, "template", None), "template_markdown", None)
    text = str(template).strip() if template else ""
    if not text:
        text = "# Refactor Template\n\nTemplate generation failed."
    return _ensure_trailing_newline(text)


def render_prediction(result: dspy.Prediction, *, mode: str = "teach") -> str:
    """Return the generated markdown for the selected analysis mode."""

    if mode == "refactor":
        return _refactor_output(result)
    return _teaching_output(result)
