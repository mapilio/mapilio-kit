# Mapilio Kit CLI Reference

This document covers every subcommand exposed by `mapilio_kit`. Run any
command with `--help` to see its full list of arguments.

```bash
mapilio_kit --help
mapilio_kit <command> --help
```

## Quick Reference

| Command | Purpose |
| --- | --- |
| `run` | Interactive "magic" mode — guides you through everything from a single menu. |
| `authenticate` | Log in / refresh credentials for your Mapilio account. |
| `doctor` | Health-check: verify ffmpeg/exiftool, Python, credentials, disk space. |
| `validate` | Pre-flight EXIF/GPS scan over a folder of images, no upload. |
| `upload` | Upload a folder of geotagged images. |
| `decompose` | Read EXIF/GPS from images and write `mapilio_image_description.json`. |
| `video_upload` | Sample frames from a video, geotag them, and upload. |
| `image_and_csv_upload` | Upload 360° panorama images with a metadata CSV. |
| `CSVprocessor` | Convert a CSV of GPS points into the expected description format. |
| `gopro360max_processor` | Convert GoPro Max `.360` videos into equirectangular frames. |
| `zip` | Bundle a processed folder into a zip ready for upload. |
| `sampler` | Extract frames from a video at a given interval. |

## Examples

### One-shot interactive flow

```bash
mapilio_kit run
```

Walks you through authentication, source selection, geotagging and upload.

### Health-check (doctor)

Run this first when something doesn't work or after a fresh install. It
verifies that ffmpeg, exiftool, Python and your credentials are all in
order and prints an actionable list of fixes.

```bash
mapilio_kit doctor                  # text report (colored)
mapilio_kit doctor --no-color       # plain text, useful in logs / CI
mapilio_kit doctor --json           # machine-readable JSON
mapilio_kit doctor --strict         # exit non-zero on any WARN
```

Exit codes: `0` everything OK, `1` warnings (only with `--strict`), `2`
at least one check failed.

### Validate a folder of images (preflight)

Walks a directory and reports problems before you upload — missing GPS
tags, missing timestamps, duplicate captures, suspicious `(0, 0)`
coordinates, and large GPS / time gaps between consecutive images.

```bash
mapilio_kit validate "/path/to/images"
mapilio_kit validate "/path/to/images" --skip_subfolders
mapilio_kit validate "/path/to/images" --json > report.json
mapilio_kit validate "/path/to/images" \
    --max_gps_gap_meters 1000 \
    --max_time_gap_seconds 600 \
    --strict
```

Exit codes: `0` clean, `1` warnings (only with `--strict`), `2` errors.

### Authenticate

```bash
# Interactive
mapilio_kit authenticate

# Non-interactive
mapilio_kit authenticate \
  --user_name "alice" \
  --user_email "alice@example.com" \
  --user_password "$MAPILIO_PASSWORD"
```

### Upload a directory of geotagged images

```bash
# First-time upload — will run decompose internally.
mapilio_kit upload "/path/to/images"

# Skip decompose if you've already produced mapilio_image_description.json.
mapilio_kit upload "/path/to/images" --processed
```

### Decompose only (write description JSON without uploading)

```bash
mapilio_kit decompose "/path/to/images"
```

### Video upload with GoPro geotag source

```bash
mapilio_kit video_upload "/path/to/videos" "/path/to/sample_images" \
    --geotag_source "gopro_videos" \
    --interpolate_directions \
    --video_sample_interval 1
```

### GoPro Max 360 (`.360`) workflow

```bash
# Step 1: convert .360 → equirectangular frames
mapilio_kit gopro360max_processor \
    --video-file ~/Desktop/GS017111.360 \
    --output-folder ~/Desktop/OutputData/ \
    --bin-dir bin

# Step 2: upload the frames with a separate GPX track
mapilio_kit upload ~/Desktop/OutputData/frames \
    --user_name "you@example.com" \
    --geotag_source "gpx" \
    --geotag_source_path "~/Desktop/gps_track.gpx"
```

### 360° panorama image + CSV

```bash
mapilio_kit image_and_csv_upload "/path/to/images" \
    --csv_path "/path/to/metadata.csv"
```

### Zip and upload (large batches)

```bash
mapilio_kit zip "/path/to/images" "/path/to/zipfolder"
mapilio_kit upload "/path/to/zipfolder" --processed
```

## See also

- [Configuration & environment variables](CONFIGURATION.md)
- [Architecture overview](ARCHITECTURE.md)
- [Docker usage](../Docker.md)
- [GoPro 360 Max details](../GoPro360Max.md)
