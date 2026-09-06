"""Regression tests for the shared duration probe."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from faceless.core.exceptions import ExternalToolError
from faceless.utils.media import probe_media_duration


@pytest.mark.parametrize(
    "output", ["0", "-0.0", "-1", "nan", "NaN", "inf", "-inf", "1e999"]
)
def test_probe_rejects_nonpositive_or_nonfinite_duration(output: str) -> None:
    with patch("faceless.utils.media.subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, output, "diagnostic")
        with pytest.raises(ExternalToolError, match="positive and finite") as exc_info:
            probe_media_duration(Path("audio.mp3"), "ffprobe")
    assert exc_info.value.details["stdout"] == output
    assert exc_info.value.details["stderr"] == "diagnostic"


@pytest.mark.parametrize("output", ["", " ", "N/A", "bad duration", "1\n2"])
def test_probe_preserves_invalid_output(output: str) -> None:
    with patch("faceless.utils.media.subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, output, "diagnostic")
        with pytest.raises(ExternalToolError, match="invalid duration") as exc_info:
            probe_media_duration(Path("audio.mp3"), "ffprobe")
    assert exc_info.value.details["stdout"] == output
    assert exc_info.value.details["return_code"] == 0
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_probe_rejects_failed_process_even_with_valid_stdout() -> None:
    with patch("faceless.utils.media.subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 7, "12.5", "broken input")
        with pytest.raises(ExternalToolError, match="probe failed") as exc_info:
            probe_media_duration(Path("audio.mp3"), "ffprobe")
    assert exc_info.value.details["return_code"] == 7
    assert exc_info.value.details["stdout"] == "12.5"
    assert exc_info.value.details["stderr"] == "broken input"


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("missing executable"),
        PermissionError("not executable"),
        OSError("process creation failed"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid encoding"),
    ],
)
def test_probe_preserves_execution_failure(error: Exception) -> None:
    with (
        patch("faceless.utils.media.subprocess.run", side_effect=error),
        pytest.raises(ExternalToolError, match="Could not run FFprobe") as exc_info,
    ):
        probe_media_duration(Path("audio.mp3"), "ffprobe")
    assert exc_info.value.__cause__ is error
    assert exc_info.value.details["error"] == str(error)
    assert exc_info.value.details["path"] == "audio.mp3"


def test_probe_preserves_timeout_diagnostics() -> None:
    error = subprocess.TimeoutExpired(
        "ffprobe", 30, output=b"partial duration", stderr=b"partial diagnostic"
    )
    with (
        patch("faceless.utils.media.subprocess.run", side_effect=error),
        pytest.raises(ExternalToolError, match="timed out") as exc_info,
    ):
        probe_media_duration(Path("audio.mp3"), "ffprobe")
    assert exc_info.value.__cause__ is error
    assert exc_info.value.details["timeout"] == 30
    assert exc_info.value.details["stdout"] == b"partial duration"
    assert exc_info.value.details["stderr"] == b"partial diagnostic"


@pytest.mark.parametrize("resolved", [None, r"C:\Tools & helpers\custom-probe.exe"])
def test_probe_resolves_configured_command_without_shell(resolved: str | None) -> None:
    executable = "custom-probe"
    media_path = Path("Alice's story & %PATH%.mp3")
    with (
        patch("faceless.utils.media.shutil.which", return_value=resolved) as which,
        patch("faceless.utils.media.subprocess.run") as run,
    ):
        run.return_value = subprocess.CompletedProcess([], 0, " 1.25\n", "")
        assert probe_media_duration(media_path, executable) == 1.25
    which.assert_called_once_with(executable)
    run.assert_called_once_with(
        [
            resolved or executable,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
