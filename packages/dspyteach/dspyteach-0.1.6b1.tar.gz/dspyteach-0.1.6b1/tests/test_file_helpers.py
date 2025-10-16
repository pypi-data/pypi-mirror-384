from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dspy_file.file_helpers import collect_source_paths, render_prediction


def _touch(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collect_source_paths_skips_hidden_and_config_files(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    allowed_file = project_root / "main.py"
    _touch(allowed_file, "print('ok')\n")

    _touch(project_root / ".env", "SECRET=1\n")
    _touch(project_root / ".venv" / "lib" / "ignore.py", "print('ignored')\n")
    _touch(project_root / "nested" / ".secrets", "hidden\n")

    collected = collect_source_paths(str(project_root))

    assert collected == [allowed_file.resolve()]


def test_hidden_files_can_be_included_with_explicit_glob(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    hidden_file = project_root / ".config" / "ci.yml"
    _touch(hidden_file, "name: ci\n")

    collected = collect_source_paths(
        str(project_root),
        include_globs=[".config/**/*.yml"],
    )

    assert collected == [hidden_file.resolve()]


def test_collect_source_paths_honors_exclude_dirs(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    kept = project_root / "keep" / "file.py"
    skipped = project_root / "skip" / "ignored.py"
    nested_skip = project_root / "nested" / "deep" / "hidden.py"
    _touch(kept, "print('keep')\n")
    _touch(skipped, "print('ignore')\n")
    _touch(nested_skip, "print('nested ignore')\n")

    collected = collect_source_paths(
        str(project_root),
        exclude_dirs=["skip", "nested/deep"],
    )
    collected_glob = collect_source_paths(
        str(project_root),
        include_globs=["**/*.py"],
        exclude_dirs=["skip", "nested/deep"],
    )

    assert collected == [kept.resolve()]
    assert collected_glob == [kept.resolve()]


def test_render_prediction_teach_mode_uses_report() -> None:
    prediction = SimpleNamespace(
        report=SimpleNamespace(report_markdown="# Brief\n\nContent."),
    )
    output = render_prediction(prediction, mode="teach")
    assert output.endswith("Content.\n")


def test_render_prediction_refactor_mode_prefers_template_markdown() -> None:
    prediction = SimpleNamespace(template_markdown="# Template\n\nValue.")
    output = render_prediction(prediction, mode="refactor")
    assert output.endswith("Value.\n")

