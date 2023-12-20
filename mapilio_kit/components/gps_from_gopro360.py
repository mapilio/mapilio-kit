"""
forked by https://github.com/aurvis/gopromax-frame-extractor
"""

import argparse
import os
import sys
import pathlib
import shutil
import subprocess
import glob
import xml.etree.ElementTree as XET
import re
import fnmatch
from arguments import general_arguments

def assert_file_exists(filename, tag=""):
    stag = "file "
    if tag == "":
        stag = "[%s]" % tag
    if not os.path.isfile(filename):
        print("%s [%s] does not exist" % (stag, filename))
        sys.exit(1)


def assert_folder_exists(folder, tag=""):
    stag = "folder "
    if tag == "":
        stag = "[%s]" % tag
    if not os.path.isdir(folder):
        print("%s [%s] does not exist" % (stag, folder))
        sys.exit(1)


def delete_directory(folder):
    shutil.rmtree(folder, ignore_errors=True)


def get_files_with_pattern(ifolder, pattern, ignore_case=True, return_full_path=True):
    if ignore_case:
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
    else:
        rule = re.compile(fnmatch.translate(pattern))
    if return_full_path:
        return sorted([os.path.join(ifolder, name) for name in os.listdir(ifolder) if rule.match(name)])
    else:
        return sorted([name for name in os.listdir(ifolder) if rule.match(name)])


def remove_files(folder, file_pattern):
    # Get a list of all the file paths that ends with .txt from in specified directory
    file_list = get_files_with_pattern(folder, file_pattern)
    # Iterate over the list of filepaths & remove each file.
    for fpath in file_list:
        try:
            os.remove(fpath)
        except:
            print("Error while deleting file : ", fpath)


def make_directory(root_folder, subfolders='', remove_if_present=False):
    if subfolders == '':
        if remove_if_present:
            delete_directory(root_folder)
        pathlib.Path(root_folder).mkdir(parents=True, exist_ok=True)
        return root_folder
    else:
        assert_folder_exists(root_folder)
        sfolders = subfolders.split('/')
        mfolder = root_folder
        if remove_if_present:
            delete_directory(os.path.join(root_folder, sfolders[0]))
        for s in sfolders:
            mfolder = os.path.join(mfolder, s)
            if not os.path.isdir(mfolder):
                pathlib.Path(mfolder).mkdir(parents=True, exist_ok=True)
        return mfolder


def run_command(cmd, show_progress=False, env=None):
    if show_progress is False:
        rinfo = subprocess.run(cmd, shell=True, stdout=open(os.devnull, "wb"), env=env)
    else:
        rinfo = subprocess.run(cmd, shell=True, env=env)
    return (rinfo.returncode == 0)


def number_of_files(directory):
    return len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])


def move_file(src, dst):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    shutil.move(src, dst)


def move_all_files(ifolder, ofolder, file_filter):
    assert_folder_exists(ifolder)
    assert_folder_exists(ofolder)
    for f in glob.glob(os.path.join(ifolder, file_filter)):
        move_file(f, ofolder)


def get_gps_date_time(xml_metadata_file):
    xroot = XET.parse(xml_metadata_file).getroot()
    gps_date_time = ""
    for x in xroot.iter('{http://ns.exiftool.ca/QuickTime/Track4/1.0/}GPSDateTime'):
        gps_date_time = x.text
        break
    return gps_date_time


def get_gpx_fmt_url():
    user = "mapilio"
    repo = "mapilio-kit"
    src_dir = "schema"
    branch = "master"
    pyfile = "gpx.fmt"

    url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{src_dir}/{pyfile}"

    if not os.path.exists(pyfile):
        subprocess.run(["wget", "--no-cache", "--backups=1", url], stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def gopro360max_stitch(video_file: str,
                       frame_rate: int,
                       output_folder: str,
                       quality: str,
                       bin_dir: str):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    frame_delta = 1.0 / frame_rate
    print(f"frame_delta: {frame_delta}")

    assert_file_exists(video_file, "video file")

    assert_folder_exists(bin_dir)

    eac_stitcher_exe = os.path.join(bin_dir, 'MAX2spherebatch')
    assert_file_exists(eac_stitcher_exe)

    make_directory(output_folder, remove_if_present=True)

    #
    # Frame Extraction
    #
    print("\n#\n# Extract Frames\n#")
    t0_folder = os.path.join(output_folder, "track0")
    t5_folder = os.path.join(output_folder, "track5")
    make_directory(t0_folder, remove_if_present=True)
    make_directory(t5_folder, remove_if_present=True)

    cmd = f"ffmpeg -i {video_file} -map 0:0 -r {frame_rate} -q:v {quality} {t0_folder}/img%04d.jpg -map 0:5 -r {frame_rate} -q:v {quality} {t5_folder}/img%04d.jpg"
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)

    #
    # Equirectangular
    #
    print("\n#\n# Compute Equirectangular Frames\n#")
    no_frames = number_of_files(t0_folder)
    print(f"number of frames extracted: {no_frames}")
    cmd = f"{eac_stitcher_exe} -w 4096 -n 1 -m {no_frames} {output_folder}/track%d/img%04d.jpg"
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)
    frames_folder = os.path.join(output_folder, "frames")
    make_directory(frames_folder, remove_if_present=True)
    move_all_files(t0_folder, frames_folder, "*_sphere.jpg")
    if number_of_files(frames_folder) == 0:
        print("no sphere files extracted.")
        sys.exit(1)
    delete_directory(t0_folder)
    delete_directory(t5_folder)

    #
    # Extract Metadata
    #
    print("\n#\n# Extract Metadata\n#")
    metadata_folder = os.path.join(output_folder, "metadata")
    make_directory(metadata_folder, remove_if_present=True)

    gps_track_file = os.path.join(metadata_folder, "gps_track.gpx")
    get_gpx_fmt_url()
    cmd = f"exiftool -ee -p gpx.fmt {video_file} > {gps_track_file}"
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)

    metadata_xml_file = os.path.join(metadata_folder, "metadata_all.xml")
    cmd = f"exiftool -ee -G3 -api LargeFileSupport=1 -X {video_file} > {metadata_xml_file}"
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)

    cmd = f"exiftool -G -a {video_file} > {metadata_folder}/metadata.txt"
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)

    #
    # ADD Metadata to the frames
    #
    print("\n#\n# Adde Metadata to the frames\n#")
    # extract gps start datetime:
    gps_start_time = get_gps_date_time(os.path.join(metadata_folder, 'metadata_all.xml'))
    assert (gps_start_time != "")
    print(f"GPSDateTime: {gps_start_time}")
    # update datetimeoriginal for all frames to the initial time first
    cmd = f'exiftool -datetimeoriginal="{gps_start_time}" {frames_folder}'
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)
    # this just increments datetime original with the frame delta
    cmd = "exiftool -fileorder FileName -ext jpg '-datetimeoriginal+<0:0:${filesequence;$_*=%f}' %s" % (
        frame_delta, frames_folder)
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)

    # geotag the images
    cmd = "exiftool -ext jpg -geotag %s '-geotime<${DateTimeOriginal}+00:00' %s" % (gps_track_file, frames_folder)
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)

    cmd = f"exiftool -CameraElevationAngle=360 " \
          f"-make=GoPro " \
          f"-model=Max " \
          f"-ProjectionType=equirectangular " \
          f"-UsePanoramaViewer=True " \
          f"-CroppedAreaImageWidthPixels=4096 " \
          f"-CroppedAreaImageHeightPixels=1344 " \
          f"-FullPanoWidthPixels=4096 " \
          f"-FullPanoHeightPixels=1344 " \
          f"-CroppedAreaLeftPixels=0 -CroppedAreaTopPixels=0 {frames_folder}"
    print(f"cmd: {cmd}")
    run_command(cmd, show_progress=False)
    remove_files(frames_folder, "*.jpg_original")

    print("\n")



def main():
    parser = argparse.ArgumentParser(description="gopro360")


    parser.add_argument('--video-file', '-vf', type=str, help='video file path', default=None)
    parser.add_argument('--output-folder', '-of', type=str, help='output folder', default='/tmp/test')
    parser.add_argument('--frame-rate', '-fps', type=int, help='how many frames to extract per frame', default=1)
    parser.add_argument('--quality', '-q', type=int, help='frame extraction quality', default=2)
    parser.add_argument('--bin-dir', '-b', type=str, help='directory that contains the MAX2spherebatch exec', default='bin/')

    args = parser.parse_args()

    gopro360max_stitch(args.video_file,args.frame_rate, args.output_folder,  args.quality, args.bin_dir)



if __name__ == "__main__":
    main()
