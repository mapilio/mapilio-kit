"""Health-check helpers used by the ``mapilio_kit doctor`` command.

The functions here are intentionally pure (no side effects beyond the system
calls they describe) so that ``base/doctor.py`` stays a thin CLI wrapper and
unit tests can exercise the underlying logic with mocks.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import typing as T
from dataclasses import asdict, dataclass, field

# These minimums match what we test on CI; older versions may "work" but are
# unsupported.
MIN_PYTHON: T.Tuple[int, int] = (3, 8)
MIN_FFMPEG: T.Tuple[int, int] = (4, 0)
MIN_EXIFTOOL: T.Tuple[int, int] = (12, 0)
MIN_FREE_DISK_BYTES: int = 1 * 1024 * 1024 * 1024  # 1 GiB

#: Status values used for individual checks.
OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class CheckResult:
    """Outcome of a single health check."""

    name: str
    status: str  # one of OK / WARN / FAIL
    message: str
    details: T.Dict[str, T.Any] = field(default_factory=dict)


@dataclass
class DoctorReport:
    """A bundle of every check executed by ``doctor``."""

    checks: T.List[CheckResult] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        """Worst status across all checks."""
        if any(c.status == FAIL for c in self.checks):
            return FAIL
        if any(c.status == WARN for c in self.checks):
            return WARN
        return OK

    def to_dict(self) -> T.Dict[str, T.Any]:
        return {
            "overall_status": self.overall_status,
            "checks": [asdict(c) for c in self.checks],
        }


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _parse_version(text: str) -> T.Optional[T.Tuple[int, ...]]:
    """Pull the first ``X.Y[.Z]`` token out of ``text``."""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    return tuple(int(p) for p in match.groups() if p is not None)


def _ge(actual: T.Tuple[int, ...], minimum: T.Tuple[int, ...]) -> bool:
    return tuple(actual[: len(minimum)]) >= minimum


def _run(
    cmd: T.Sequence[str],
    timeout: float = 5.0,
) -> T.Tuple[int, str, str]:
    """Run ``cmd`` and return (returncode, stdout, stderr).

    Returns ``(-1, "", str(error))`` if the binary is missing or the run
    times out. Never raises.
    """
    try:
        proc = subprocess.run(  # noqa: S603 — args are fixed by callers
            list(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return -1, "", f"not found: {exc}"
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except OSError as exc:  # pragma: no cover - very unusual
        return -1, "", str(exc)
    return proc.returncode, proc.stdout, proc.stderr


# --------------------------------------------------------------------------- #
# Individual checks                                                           #
# --------------------------------------------------------------------------- #


def check_python_version(
    version_info: T.Tuple[int, ...] = sys.version_info[:3],
    minimum: T.Tuple[int, int] = MIN_PYTHON,
) -> CheckResult:
    actual = tuple(version_info)
    pretty = ".".join(str(p) for p in actual)
    if _ge(actual, minimum):
        return CheckResult(
            name="python",
            status=OK,
            message=f"Python {pretty}",
            details={"version": pretty},
        )
    return CheckResult(
        name="python",
        status=FAIL,
        message=(
            f"Python {pretty} is below the supported minimum "
            f"{minimum[0]}.{minimum[1]}"
        ),
        details={"version": pretty, "minimum": list(minimum)},
    )


def check_kit_version(version: str) -> CheckResult:
    return CheckResult(
        name="mapilio_kit",
        status=OK,
        message=f"mapilio-kit {version}",
        details={"version": version},
    )


def _check_external_binary(
    name: str,
    args_for_version: T.Sequence[str],
    minimum: T.Tuple[int, int],
    runner: T.Callable[[T.Sequence[str]], T.Tuple[int, str, str]] = _run,
    which: T.Callable[[str], T.Optional[str]] = shutil.which,
) -> CheckResult:
    binary_path = which(name)
    if not binary_path:
        return CheckResult(
            name=name,
            status=FAIL,
            message=f"{name} not found in PATH",
            details={"path": None},
        )
    rc, stdout, stderr = runner([binary_path, *args_for_version])
    output = stdout if stdout else stderr
    version = _parse_version(output) if rc != -1 else None
    if version is None:
        return CheckResult(
            name=name,
            status=WARN,
            message=f"{name} found at {binary_path} but version could not be parsed",
            details={"path": binary_path, "raw_output": output[:200]},
        )
    pretty = ".".join(str(p) for p in version)
    if _ge(version, minimum):
        return CheckResult(
            name=name,
            status=OK,
            message=f"{name} {pretty} ({binary_path})",
            details={"path": binary_path, "version": pretty},
        )
    return CheckResult(
        name=name,
        status=WARN,
        message=(
            f"{name} {pretty} is below the recommended minimum "
            f"{minimum[0]}.{minimum[1]} ({binary_path})"
        ),
        details={
            "path": binary_path,
            "version": pretty,
            "minimum": list(minimum),
        },
    )


def check_ffmpeg(
    runner: T.Callable[[T.Sequence[str]], T.Tuple[int, str, str]] = _run,
    which: T.Callable[[str], T.Optional[str]] = shutil.which,
) -> CheckResult:
    return _check_external_binary("ffmpeg", ["-version"], MIN_FFMPEG, runner, which)


def check_exiftool(
    runner: T.Callable[[T.Sequence[str]], T.Tuple[int, str, str]] = _run,
    which: T.Callable[[str], T.Optional[str]] = shutil.which,
) -> CheckResult:
    return _check_external_binary("exiftool", ["-ver"], MIN_EXIFTOOL, runner, which)


def check_disk_space(
    path: str = ".",
    minimum_bytes: int = MIN_FREE_DISK_BYTES,
    disk_usage: T.Callable[[str], T.Any] = shutil.disk_usage,
) -> CheckResult:
    try:
        usage = disk_usage(path)
        free = int(usage.free)
    except OSError as exc:
        return CheckResult(
            name="disk",
            status=WARN,
            message=f"Could not check disk space for {path!r}: {exc}",
            details={"path": path, "error": str(exc)},
        )
    free_gb = free / (1024**3)
    if free >= minimum_bytes:
        return CheckResult(
            name="disk",
            status=OK,
            message=f"{free_gb:.1f} GiB free on {path}",
            details={"path": path, "free_bytes": free},
        )
    return CheckResult(
        name="disk",
        status=WARN,
        message=(
            f"Only {free_gb:.2f} GiB free on {path} (recommended ≥ "
            f"{minimum_bytes / (1024**3):.1f} GiB)"
        ),
        details={
            "path": path,
            "free_bytes": free,
            "minimum_bytes": minimum_bytes,
        },
    )


def check_credentials(
    user_loader: T.Optional[T.Callable[[], T.List[T.Dict[str, T.Any]]]] = None,
) -> CheckResult:
    """Check that there's at least one authenticated Mapilio user.

    The loader is injected so tests don't need to touch the real config
    file; in production we use ``components.auth.login.list_all_users``.
    """
    if user_loader is None:
        # Imported lazily so doctor doesn't drag in heavy modules at import
        # time and so unit tests can run without the auth subsystem.
        from mapilio_kit.components.auth.login import list_all_users

        user_loader = list_all_users  # type: ignore[assignment]

    try:
        users = list(user_loader())
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        return CheckResult(
            name="credentials",
            status=WARN,
            message=f"Could not read Mapilio credentials: {exc}",
            details={"error": str(exc)},
        )

    valid = [u for u in users if "SettingsEmail" in u]
    if not valid:
        return CheckResult(
            name="credentials",
            status=WARN,
            message=(
                "No authenticated Mapilio user found. "
                "Run 'mapilio_kit authenticate' to sign in."
            ),
            details={"user_count": 0},
        )

    emails = [u.get("SettingsEmail") for u in valid]
    return CheckResult(
        name="credentials",
        status=OK,
        message=f"{len(valid)} authenticated user(s): {', '.join(str(e) for e in emails)}",
        details={"user_count": len(valid), "emails": emails},
    )


def check_telemetry(env: T.Optional[T.Mapping[str, str]] = None) -> CheckResult:
    env = env if env is not None else os.environ
    disabled = env.get("MAPILIO_KIT_DISABLE_TELEMETRY", "").lower() in {
        "1", "true", "yes", "on",
    }
    dsn_set = bool(env.get("MAPILIO_KIT_SENTRY_DSN", "").strip())
    if disabled:
        msg = "Sentry telemetry disabled (MAPILIO_KIT_DISABLE_TELEMETRY)"
    elif dsn_set:
        msg = "Sentry telemetry enabled (MAPILIO_KIT_SENTRY_DSN set)"
    else:
        msg = "Sentry telemetry off (no DSN configured)"
    return CheckResult(
        name="telemetry",
        status=OK,
        message=msg,
        details={"disabled": disabled, "dsn_configured": dsn_set},
    )


def check_platform() -> CheckResult:
    return CheckResult(
        name="platform",
        status=OK,
        message=f"{platform.system()} {platform.release()} ({platform.machine()})",
        details={
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    )


# --------------------------------------------------------------------------- #
# Aggregator                                                                  #
# --------------------------------------------------------------------------- #


def run_all_checks(version: str) -> DoctorReport:
    """Run every health check and return a populated ``DoctorReport``."""
    return DoctorReport(
        checks=[
            check_platform(),
            check_python_version(),
            check_kit_version(version),
            check_ffmpeg(),
            check_exiftool(),
            check_disk_space(),
            check_credentials(),
            check_telemetry(),
        ]
    )


# --------------------------------------------------------------------------- #
# Rendering                                                                   #
# --------------------------------------------------------------------------- #

_STATUS_GLYPH = {OK: "✓", WARN: "!", FAIL: "✗"}


def render_text(report: DoctorReport, *, use_color: bool = True) -> str:
    """Format a report as human-readable text suitable for stdout."""
    try:
        from colorama import Fore, Style
        color_for = {
            OK: Fore.GREEN,
            WARN: Fore.YELLOW,
            FAIL: Fore.RED,
        }
        reset = Style.RESET_ALL
    except ImportError:  # pragma: no cover
        color_for = {OK: "", WARN: "", FAIL: ""}
        reset = ""

    if not use_color:
        color_for = {OK: "", WARN: "", FAIL: ""}
        reset = ""

    lines: T.List[str] = ["Mapilio Kit doctor report", "-" * 28]
    for check in report.checks:
        glyph = _STATUS_GLYPH.get(check.status, "?")
        color = color_for.get(check.status, "")
        lines.append(f"  {color}{glyph}{reset} {check.name:<14} {check.message}")
    lines.append("-" * 28)
    overall_color = color_for.get(report.overall_status, "")
    lines.append(f"Overall: {overall_color}{report.overall_status.upper()}{reset}")
    return "\n".join(lines)
