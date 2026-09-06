"""Validated duration probing shared by media services."""

import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from faceless.core.exceptions import ExternalToolError
from faceless.utils.logging import get_logger

logger = get_logger(__name__)


def _probe_error(message: str, details: dict[str, Any]) -> ExternalToolError:
    logger.error(message, **details)
    return ExternalToolError(message, details=details)


def probe_media_duration(media_path: Path, ffprobe_path: str) -> float:
    """Read a positive, finite media duration using the configured FFprobe.

    Args:
        media_path: Audio or video file to inspect.
        ffprobe_path: Executable path or command name, without shell quoting.

    Returns:
        Measured duration in seconds.

    Raises:
        ExternalToolError: If FFprobe cannot run, fails, or returns invalid timing.
            Details preserve the command, path, and available process diagnostics.
    """
    executable = ffprobe_path
    if not (Path(executable).is_absolute() or "/" in executable or "\\" in executable):
        executable = shutil.which(executable) or executable
    command = [
        executable,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    details: dict[str, Any] = {"path": str(media_path), "command": command}
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=30, shell=False
        )
    except subprocess.TimeoutExpired as exc:
        details.update(timeout=exc.timeout, stdout=exc.stdout, stderr=exc.stderr)
        raise _probe_error("FFprobe duration probe timed out", details) from exc
    except (OSError, UnicodeError) as exc:
        details["error"] = str(exc)
        raise _probe_error("Could not run FFprobe duration probe", details) from exc

    details.update(
        return_code=result.returncode, stdout=result.stdout, stderr=result.stderr
    )
    if result.returncode != 0:
        raise _probe_error("FFprobe duration probe failed", details)
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise _probe_error("FFprobe returned an invalid duration", details) from exc
    if not math.isfinite(duration) or duration <= 0:
        raise _probe_error("FFprobe duration must be positive and finite", details)
    return duration
