# refactor_analyzer.py - DSPy module that prepares per-file refactor prompt templates
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import dspy

from .prompts import load_prompt_text


class RefactorTemplateSignature(dspy.Signature):
    """Generate a reusable refactor prompt template from a source document."""

    file_path: str = dspy.InputField(desc="Path to the source file for context")
    file_content: str = dspy.InputField(desc="Full raw text of the file")

    template_markdown: str = dspy.OutputField(
        desc="Markdown template with numbered placeholders and section scaffolding"
    )


@dataclass
class RefactorTeachingConfig:
    """Configuration for the refactor template generator."""

    max_tokens: int = 8000
    temperature: float | None = 0.7
    top_p: float | None = 0.80
    n_completions: int | None = None
    extra_lm_kwargs: dict[str, Any] = field(default_factory=dict)

    def lm_kwargs(self) -> dict[str, Any]:
        """Return the language model arguments for DSPy modules."""

        kwargs: dict[str, Any] = {**self.extra_lm_kwargs, "max_tokens": self.max_tokens}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.n_completions is not None:
            kwargs["n"] = self.n_completions
        return kwargs


@lru_cache(maxsize=1)
def _load_default_template() -> str:
    """Load the bundled refactor prompt template text."""

    return load_prompt_text(None).strip()


def _ensure_template_text(value: str | None) -> str:
    if value and value.strip():
        text = value.rstrip()
    else:
        text = "# Refactor Template\n\nTemplate generation failed."
    return text if text.endswith("\n") else text + "\n"


class FileRefactorAnalyzer(dspy.Module):
    """Generate a refactor-focused prompt template for a single file."""

    def __init__(
        self,
        *,
        template_text: str | None = None,
        config: RefactorTeachingConfig | None = None,
    ) -> None:
        super().__init__()
        self.config = config or RefactorTeachingConfig()
        instructions = template_text.strip() if template_text else _load_default_template()
        signature = RefactorTemplateSignature.with_instructions(instructions)
        self.generator = dspy.ChainOfThought(signature, **self.config.lm_kwargs())

    def forward(self, *, file_path: str, file_content: str) -> dspy.Prediction:
        raw_prediction = self.generator(
            file_path=file_path,
            file_content=file_content,
        )

        template_markdown = _ensure_template_text(
            getattr(raw_prediction, "template_markdown", None)
        )

        return dspy.Prediction(
            template=raw_prediction,
            template_markdown=template_markdown,
        )
