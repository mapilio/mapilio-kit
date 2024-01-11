<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mapilio Kit Docker Setup and Usage</title>
</head>
<body>

  <h1>Mapilio Kit Docker Setup and Usage</h1>

  <p>This repository contains the necessary setup for using Mapilio Kit within a Docker environment. Follow the steps below to set up and use the kit for processing images from a GoPro 360 Max camera.</p>
  <p>These steps below is an example for GoPro360MaxPro, however, right after finishing the getting started part, you may use other options by modifying the steps. (e.g. if you want to use mapilio_kit run command, you may simply use it like this: <strong>sudo docker exec -it kit mapilio_kit run</strong></p>

  <h2>Prerequisites</h2>
  <ul>
    <li><a href="https://www.docker.com/" target="_blank">Docker</a></li>
    <li><a href="https://docs.docker.com/compose/" target="_blank">Docker Compose</a></li>
  </ul>

  <h2>Getting Started</h2>
  <ol>
    <li>Clone the repository:</li>
  </ol>

  <pre><code>git clone https://github.com/mapilio/mapilio-kit.git
cd mapilio-kit/docker</code></pre>

  <ol start="2">
    <li>Build the Docker image:</li>
  </ol>

  <pre><code>docker-compose up -d  --build</code></pre>

  <p>Now, you are in the bash shell, and you can proceed with the Mapilio Kit commands.</p>

  <h2>Mapilio Kit Commands</h2>

  <ol>
    <li><strong>Authentication:</strong></li>
  </ol>

  <pre><code>sudo docker exec -it kit mapilio_kit authenticate</code></pre>

  <ol start="2">
    <li><strong>Process GoPro 360 Max Video:</strong></li>
  </ol>

  <pre><code>sudo docker exec -it kit mapilio_kit gopro360max_process --video-file data/<em>&lt;your_file_name&gt;</em> --output-folder OutputData/ --bin-dir bin</code></pre>

  <ol start="3">
    <li><strong>Upload Processed Images:</strong></li>
  </ol>

  <pre><code>sudo docker exec -it kit mapilio_kit upload OutputData/frames --geotag_source "gpx" --geotag_source_path "OutputData/metadata/gps_track.gpx"</code></pre>

  <p>Make sure to replace <em>&lt;your_file_name&gt;</em> with the actual name of your GoPro 360 Max video file.</p>

  <h2>Important Note</h2>
  <p>Before running the commands, ensure to modify the Docker Compose file (<code>docker-compose.yml</code>) with your local video absolute path <strong>(Example path: 'C:\Videos\Gopro360videos\')</strong>:</p>

  <pre><code>  volumes:
      - &lt;your_local_videos_path&gt;:/app/data/<em></em></code></pre>

  <p>Replace <em>&lt;your_local_videos_path&gt;</em> with the path on your local machine where the GoPro 360 Max video is located.</p>

</body>
</html>
