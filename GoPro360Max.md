# How to 360 max images upload to Mapilio

Firstly install mapilio_kit 
```bash
pip install mapilio_kit>=2.0.9
```
Then download and install dependency [max_extractor_install](https://github.com/mapilio/mapilio-kit/blob/main/max_extractor_install.sh)
```bash
source max_extractor_install.sh
```

Now you can follow [Readme file](https://github.com/mapilio/mapilio-kit/blob/main/README.md) but for now we just upload 360 max pro video and images.


note that, do not set the same path as the video file path with the output folder path.

- --video-file {video file path}
- --output-folder {output frames path}
- --bin-dir {equirectanguler bin path}

```bash
mapilio_kit gopro360max_process --video-file ~/Desktop/sample.360 --output-folder ~/Desktop/OutputData/ --bin-dir bin
```

Finally, we can upload frames

```bash
mapilio_kit upload ~/Desktop/OutputData/frames --user_name="username@mapilio.com" \
                    --geotag_source "gpx" \
                    --geotag_source_path "~Desktop/gps_track.gpx"
```

Congratulations everything is done.