from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from dspy_file import analyze_file_cli


def test_probe_openai_provider_success() -> None:
    mock_response = mock.MagicMock()
    urlopen_mock = mock.MagicMock()
    urlopen_mock.return_value.__enter__.return_value = mock_response

    with mock.patch(
        "dspy_file.analyze_file_cli.request.urlopen", urlopen_mock
    ):
        analyze_file_cli._probe_openai_provider("http://localhost:1234/v1", "token")

    urlopen_mock.assert_called_once()


def test_probe_openai_provider_raises_on_failure() -> None:
    with mock.patch(
        "dspy_file.analyze_file_cli.request.urlopen",
        side_effect=analyze_file_cli.urlerror.URLError("connection refused"),
    ):
        with pytest.raises(analyze_file_cli.ProviderConnectivityError):
            analyze_file_cli._probe_openai_provider("http://localhost:1234/v1", "token")


def test_main_exits_early_when_lmstudio_unreachable(tmp_path: Path) -> None:
    source = tmp_path / "example.md"
    source.write_text("content", encoding="utf-8")

    with mock.patch.object(
        analyze_file_cli,
        "_probe_openai_provider",
        side_effect=analyze_file_cli.ProviderConnectivityError("unreachable"),
    ), mock.patch.object(analyze_file_cli, "configure_model") as configure_mock:
        exit_code = analyze_file_cli.main(
            ["--provider", "lmstudio", str(source)]
        )

    assert exit_code == 1
    configure_mock.assert_not_called()
