"""Bundled prompt templates for dspyteach."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

try:  # Python 3.9+
    from importlib import resources
except ImportError:  # pragma: no cover
    import importlib_resources as resources  # type: ignore[assignment]

PROMPT_SUFFIXES = (".md", ".txt")


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    path: Path


def _bundled_directory() -> Path:
    return Path(resources.files("dspy_file.prompts"))


def list_bundled_prompts() -> List[PromptTemplate]:
    directory = _bundled_directory()
    prompts: List[PromptTemplate] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and entry.suffix.lower() in PROMPT_SUFFIXES:
            prompts.append(PromptTemplate(name=entry.stem, path=entry))
    return prompts


def resolve_prompt_path(prompt_arg: str | None) -> Path:
    if not prompt_arg:
        prompts = list_bundled_prompts()
        if not prompts:
            raise FileNotFoundError("No bundled prompt templates found.")
        return prompts[0].path

    provided = Path(prompt_arg).expanduser()
    if provided.is_file():
        return provided.resolve()

    directory = _bundled_directory()
    bundle_path = directory / prompt_arg
    if bundle_path.is_file():
        return bundle_path.resolve()

    for suffix in PROMPT_SUFFIXES:
        candidate = directory / f"{prompt_arg}{suffix}"
        if candidate.is_file():
            return candidate.resolve()

    for template in list_bundled_prompts():
        if template.name == prompt_arg:
            return template.path.resolve()

    raise FileNotFoundError(f"Prompt template not found: {prompt_arg}")


def load_prompt_text(prompt_arg: str | None) -> str:
    path = resolve_prompt_path(prompt_arg)
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Prompt template is empty: {path}")
    return text


__all__ = [
    "PromptTemplate",
    "list_bundled_prompts",
    "resolve_prompt_path",
    "load_prompt_text",
]
