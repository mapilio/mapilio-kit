# Architecture Overview

Mapilio Kit is organised as a thin CLI on top of a layered library. This
document explains the moving parts so contributors know where to make
changes.

## High-level layout

```
mapilio_kit/
├── __main__.py          # CLI entry point + command dispatch
├── base/                # Top-level command implementations (uploader,
│                        #   decomposer, video_loader, run_mapi, ...)
└── components/          # Reusable building blocks
    ├── auth/            # Login & token management
    ├── geotagging/      # GPS / GPX / GoPro location parsing
    ├── metadata/        # EXIF read/write
    ├── processing/      # FFmpeg wrappers, frame extraction
    ├── upload/          # Chunked upload, resume, progress
    ├── blending/        # Equirectangular merging for 360°
    ├── ipc/             # Inter-process helpers
    ├── logs/, logger.py # Logging setup
    ├── utilities/       # Shared helpers (point math, CSV, types, errors)
    └── version.py       # Single source of truth for the package version
```

## Request flow

A typical upload looks like this:

```
mapilio_kit upload ./images
        │
        ▼
mapilio_kit/__main__.py            (parse args, dispatch)
        │
        ▼
mapilio_kit/base/uploader.py       (orchestrates the run)
        │
        ├── components/auth/login.py            (load credentials)
        ├── components/metadata/                (read EXIF tags)
        ├── components/geotagging/              (resolve GPS per image)
        ├── components/utilities/utilities.py   (FOV / aspect / hashing)
        └── components/upload/                  (chunked HTTP to Mapilio)
```

`run` (the magic mode) sits at `base/run_mapi.py` and is essentially a
TUI built on `simple-term-menu` that calls the same building blocks.

## Geotag sources

`components/geotagging/` chooses the right parser based on
`--geotag_source`:

- `images` — read EXIF GPS tags directly from the image files (default).
- `gpx` — match a GPX track to images by capture timestamp.
- `gopro_videos` — extract a GPS track from GoPro telemetry (GPMF).
- `gopro360max` — same, but for `.360` files via the bundled
  `MAX2spherebatch` extractor.

Add a new source by:

1. Adding a parser in `components/geotagging/` that yields `Point` instances
   (see `components/utilities/point.py`).
2. Wiring it into `geotag_property_handler.py`.
3. Exposing the new `--geotag_source` value in `components/utilities/arguments.py`.

## Native binaries

The build pulls in `extras/max2sphere-batch` and compiles
`MAX2spherebatch` into `mapilio_kit/base/bin/`. This step is wrapped by
`MakeBuild` in `setup.py` and only runs on Linux. Windows and macOS use
the prebuilt copy distributed with the wheel.

## Telemetry

Sentry is initialised in `__main__.py` _only_ when
`MAPILIO_KIT_SENTRY_DSN` is set and `MAPILIO_KIT_DISABLE_TELEMETRY` is
unset. See [`CONFIGURATION.md`](CONFIGURATION.md) for the full list of
relevant environment variables.

## Tests

Tests live under `tests/` and use pytest. They are designed to run on a
"thin" install — heavy optional dependencies (`calculation`, GoPro
binaries, ffmpeg) are stubbed in `tests/conftest.py`. Run with:

```bash
pytest                       # unit tests
pytest --run-integration     # also run integration tests (need real tools)
```

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the full development
workflow.
