"""``mapilio_kit doctor`` — health-check command.

Verifies the local environment is set up correctly: Python version, ffmpeg
and exiftool availability, disk space, authentication state, telemetry
configuration. Designed so new users get an actionable list of fixes
rather than a cryptic failure mid-upload.
"""

from __future__ import annotations

import argparse
import json
import sys

from mapilio_kit.components.utilities.doctor import (
    FAIL,
    WARN,
    render_text,
    run_all_checks,
)
from mapilio_kit.components.version import VERSION


class Doctor:
    name = "doctor"
    help = "Check the local environment for missing tools or misconfiguration"

    def fundamental_arguments(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group("doctor options")
        group.add_argument(
            "--json",
            dest="output_json",
            action="store_true",
            default=False,
            help="Emit a machine-readable JSON report instead of text.",
        )
        group.add_argument(
            "--no-color",
            dest="no_color",
            action="store_true",
            default=False,
            help="Disable ANSI colors in the text report.",
        )
        group.add_argument(
            "--strict",
            dest="strict",
            action="store_true",
            default=False,
            help="Exit with a non-zero status if any check is WARN or FAIL.",
        )

    def perform_task(self, vars_args: dict) -> None:
        report = run_all_checks(VERSION)

        if vars_args.get("output_json"):
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(render_text(report, use_color=not vars_args.get("no_color", False)))

        if report.overall_status == FAIL:
            sys.exit(2)
        if vars_args.get("strict") and report.overall_status == WARN:
            sys.exit(1)
