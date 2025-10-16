# signatures.py - DSPy signatures focused on extracting teachings from a single file
from typing import List

import dspy


class FileOverview(dspy.Signature):
    """Summarize the file structure and core narrative with room for depth."""

    file_path: str = dspy.InputField(desc="Path to the source file")
    file_content: str = dspy.InputField(desc="Full raw text of the file")

    overview: str = dspy.OutputField(
        desc="Detailed multi-section overview (aim for 4-6 paragraphs capturing scope, intent, and flow)"
    )
    section_notes: List[str] = dspy.OutputField(
        desc="Comprehensive bullet list summarizing each major section, include headings when possible"
    )


class TeachingPoints(dspy.Signature):
    """Extract teachable concepts, workflows, and cautions."""

    file_content: str = dspy.InputField(desc="Full raw text of the file")

    key_concepts: List[str] = dspy.OutputField(desc="Essential ideas learners must retain")
    practical_steps: List[str] = dspy.OutputField(desc="Actionable steps or workflows described")
    pitfalls: List[str] = dspy.OutputField(desc="Warnings, gotchas, or misconceptions to avoid")
    references: List[str] = dspy.OutputField(desc="Follow-up links, exercises, or related material")
    usage_patterns: List[str] = dspy.OutputField(
        desc="Common usage patterns, scenarios, or recipes that appear"
    )
    key_functions: List[str] = dspy.OutputField(
        desc="Important functions, classes, or hooks with quick rationale"
    )
    code_walkthroughs: List[str] = dspy.OutputField(
        desc="Short code snippets or walkthroughs learners should discuss"
    )
    integration_notes: List[str] = dspy.OutputField(
        desc="Guidance for connecting this file with the rest of the system"
    )
    testing_focus: List[str] = dspy.OutputField(
        desc="Areas that need tests, validations, or monitoring"
    )


class TeachingReport(dspy.Signature):
    """Compose a concise but comprehensive markdown teaching brief."""

    file_path: str = dspy.InputField(desc="Original file path for context header")
    overview: str = dspy.InputField()
    section_notes: List[str] = dspy.InputField()
    key_concepts: List[str] = dspy.InputField()
    practical_steps: List[str] = dspy.InputField()
    pitfalls: List[str] = dspy.InputField()
    references: List[str] = dspy.InputField()
    usage_patterns: List[str] = dspy.InputField()
    key_functions: List[str] = dspy.InputField()
    code_walkthroughs: List[str] = dspy.InputField()
    integration_notes: List[str] = dspy.InputField()
    testing_focus: List[str] = dspy.InputField()

    report_markdown: str = dspy.OutputField(desc="Final markdown document capturing key teachings")
