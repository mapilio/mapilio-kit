# Mapilio Kit

Mapilio Kit is a library for processing and uploading images to [Mapilio](https://www.mapilio.com/).
<!DOCTYPE html>


<h1>Kit Contents</h1>
<ul>
  <li><a href="#introduction">Introduction</a></li>
  <li><a href="#getting-started">Getting Started</a></li>
  <li><a href="#usage">Usage</a></li>
  <li><a href="https://github.com/mapilio/mapilio-kit-v2/blob/main/CONTRIBUTING.md">Contributing</a></li>
  <li><a href="#license">License</a></li>
</ul>

<hr>

<h1 id="introduction">Introduction</h1>

<p>Our Image Uploader with GPS Metadata is a powerful tool designed to simplify the process of uploading and managing images, while also preserving and utilizing valuable location-based information embedded in photos. With the increasing popularity of geotagging in modern cameras and smartphones, GPS metadata in images can provide valuable context and enhance the user experience. Whether you're a photographer, a traveler, or simply someone who values the story behind each image, our uploader has you covered.
<hr>

<h1 id="getting-started">Getting Started</h1>

<p>These instructions will help contributors get a copy of your project up and running on their local machine for development and testing purposes.</p>

<ol>
  <li><strong>Prerequisites:</strong>
    <p>To upload images to Mapilio, an account is required and can be created <a href="https://www.mapilio.com/signup" target="_blank">here</a>. When
    using the kits for the first time, user authentication is required. You will be prompted to enter your account
    credentials.</p>
  </li>
  <li><strong>Installation:</strong>
    <p>via Pip on Ubuntu + 18.04 and Python (3.6 and above) and git are required:</p>
    <pre><code># Installation commands
git clone https://github.com/mapilio/mapilio-kit-v2.git
cd mapilio-kit-v2
chmod +x install.sh
source ./install.sh
</code></pre>
  </li>
  <li>
    <strong>Necessary tools:</strong>
<p>To process images or videos, you will also need to install <code>ffmpeg</code> and <code>exiftool</code>.</p>

<p>You can download <code>ffmpeg</code> from <a href="https://ffmpeg.org/download.html">here</a>. Make sure it is executable and put the downloaded binaries in your <code>$PATH</code>. You can also install <code>ffmpeg</code> with your favorite package manager. For example:</p>

<h4>On Windows:</h4>
<p>Follow the <a href="https://www.wikihow.com/Install-FFmpeg-on-Windows">ffmeg</a> and <a href="https://exiftool.org/install.html#Windows">exiftool</a> installation guides.</p>

<h4>On macOS, use Homebrew:</h4>
<pre>
brew install ffmpeg
brew install exiftool
</pre>

<h4>On Debian/Ubuntu:</h4>
<pre>
sudo apt install ffmpeg
sudo apt install exiftool
</pre>

<h4>On Windows:</h4>
<p>Open PowerShell:</p>
<pre>
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
choco install ffmpeg
choco install exiftool
</pre>
</ol>



<h1 id="usage">Usage</h1>
<hr>
<h2>Magic Usage</h2>
<p>To use basic usage simply run this command below:</p>
<h4>Examples</h4>
<pre><code>mapilio_kit run
</code></pre>

<h2>Advance Usage</h2>

<h3>User Authentication</h3>

<p>To upload images to mapilio, an account is required and can be created <a href="https://www.mapilio.com/signup" target="_blank">here</a>. When using the tools for the first time, user authentication is required. You will be prompted to enter your account credentials.</p>
<h4>Examples</h4>
<p>Authenticate new user:</p>
<pre><code>mapilio_kit authenticate
</code></pre>
<p>Authenticate for user `user_name`. If the user is already authenticated, it will update the credentials in the config:</p>
<pre><code>mapilio_kit authenticate --user_name "mapilio_user_mail"
</code></pre>

<h3>Images upload</h3>

<p>Upload command also works for timelapse images.If you haven't processed your images, please use this command below</p>
<h4>Examples</h4>
<pre><code>mapilio_kit upload "path/to/images" 
</code></pre>

<p>If you have processed your images already, use this one instead</p>
<h4>Examples</h4>
<pre><code>mapilio_kit upload "path/to/images" --processed
</code></pre>

<h3>Video Images upload</h3>
<p>
Video Support Devices: GoPro Hero 9-8-7 Black and 360, and other devices that support GPS metadata.
</p>

<h4>Examples</h4>

<ol>
<li>
Sample GoPro videos in directory path/to/videos/ into import path (must be created before starting)path/to/sample_images/ at a sampling rate 1 seconds, i.e. two frames every second, reading geotag data from the GoPro videos in path/to/videos/
</li>


<pre><code>mapilio_kit video_upload "path/to/videos/" "path/to/sample_images/" \
    --geotag_source "gopro_videos" \
    --interpolate_directions \
    --video_sample_interval 1
</code></pre>
<li> 
Checking path/to/sample_images/ images and mapilio_image_description.json then run under command
</ol>
<pre><code>mapilio_kit video_upload "path/to/sample_images/" --desc_path "mapilio_image_description.json" --processed</code></pre>

### **GoPro Max .360 videos**

#### Must be installed with this method `./max_extractor_install.sh`

1. First, create equirectangular convert script such as below

python script config

- --video-file {video file path}
- --output-folder {output frames path}
- --bin-dir {equirectanguler bin path}

```shell
mapilio_kit gopro360max_process --video-file ~/Desktop/GS017111.360 --output-folder ~/Desktop/OutputData/ --bin-dir ../../bin
```

2. Now we can upload frames

```shell
mapilio_kit upload ~/Desktop/OutputData/frames --user_name="username@mapilio.com" \
                    --geotag_source "gpx" \
                    --geotag_source_path "~Desktop/gps_track.gpx"

```

<h3>Decompose Images</h3>
<p>
The decompose command geotags images in the given directory. It extracts the required and optional metadata from image EXIF (or the other supported geotag sources), and writes all the metadata (or process errors) in an image description file, which will be read during upload.</p>
<h4>Examples</h4>
<pre><code>mapilio_kit decompose "path/to/images" 
</code></pre>


<h3>360 panorama image upload</h3>
<p>
Check the CSV format <a href="https://github.com/mapilio/mapilio-kit-v2/blob/main/schema/panoromic_image_description_shecma.csv">panoramic image description schema.</a>
</p>
<h4>Examples</h4>
<pre><code>mapilio_kit image_and_csv_upload "path/to/images" --csv_path "path/to/test.csv" --user_name "example@mapilio.com"
</code></pre>


<h3>Zip and upload</h3>

<h4>Examples</h4>
<pre><code>mapilio_kit zip  "path/to/images"  "path/to/zipfolder"
mapiio_kit upload "path/to/zipfolder" --proccessed
</code></pre>

<hr>

<h2 id="license">License</h2>

<p>This project is licensed under the MIT LICENSE - see the <code>LICENSE.md</code> file for details.</p>
