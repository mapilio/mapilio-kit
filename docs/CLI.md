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
