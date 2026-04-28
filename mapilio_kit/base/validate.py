"""``mapilio_kit validate`` — pre-flight EXIF/GPS check.

Walks a directory of images and reports problems (missing GPS tags, missing
timestamps, duplicate captures, suspicious coordinates, large GPS gaps)
without modifying anything. Designed to be run before ``upload`` so users
catch problems early.
"""

from __future__ import annotations

import argparse
import json
import sys
import typing as T

from mapilio_kit.components.utilities.validator import (
    MAX_GPS_GAP_METERS,
    MAX_TIME_GAP_SECONDS,
    build_report,
    find_images,
    read_image_exif,
    render_text,
    validate_records,
)


class Validate:
    name = "validate"
    help = "Run pre-flight EXIF/GPS checks on a directory of images"

    def fundamental_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "import_path",
            nargs="?",
            help="Directory containing the images to validate",
        )
        group = parser.add_argument_group("validate options")
        group.add_argument(
            "--skip_subfolders",
            action="store_true",
            default=False,
            help="Only validate images in the top-level directory.",
        )
        group.add_argument(
            "--max_gps_gap_meters",
            type=float,
            default=MAX_GPS_GAP_METERS,
            help=(
                "Warn when consecutive images are more than this many metres "
                "apart (default: %(default)s)."
            ),
        )
        group.add_argument(
            "--max_time_gap_seconds",
            type=float,
            default=MAX_TIME_GAP_SECONDS,
            help=(
                "Warn when consecutive images are more than this many seconds "
                "apart (default: %(default)s)."
            ),
        )
        group.add_argument(
            "--json",
            dest="output_json",
            action="store_true",
            default=False,
            help="Emit a machine-readable JSON report.",
        )
        group.add_argument(
            "--strict",
            dest="strict",
            action="store_true",
            default=False,
            help="Exit with non-zero status if any warnings are reported.",
        )

    def perform_task(self, vars_args: dict) -> None:
        path = vars_args.get("import_path")
        if not path:
            raise SystemExit("validate: import_path is required")

        images = find_images(
            path, skip_subfolders=bool(vars_args.get("skip_subfolders"))
        )
        records: T.List = [read_image_exif(p) for p in images]
        issues = validate_records(
            records,
            max_gap_meters=float(vars_args.get("max_gps_gap_meters", MAX_GPS_GAP_METERS)),
            max_time_gap_seconds=float(
                vars_args.get("max_time_gap_seconds", MAX_TIME_GAP_SECONDS)
            ),
        )
        report = build_report(records, issues)

        if vars_args.get("output_json"):
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(render_text(report))

        if report.has_errors:
            sys.exit(2)
        if vars_args.get("strict") and report.has_warnings:
            sys.exit(1)
