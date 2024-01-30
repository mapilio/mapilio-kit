import os
from tqdm import tqdm
from data_format import DataFormat, CsvFormat
from calculation.distance import Distance
import csv
import random
import string
import hashlib
import json
import pandas as pd

def photo_uuid_creater(time: str, image_name: str) -> str:
    """
    :param time: Capture time
    :param image_name: Image name
    :return: Unique image name
    """
    code = f'{image_name}--{time}'
    hash_object = hashlib.md5(code.encode())
    photo_uuid = hash_object.hexdigest()
    return photo_uuid


def unique_sequence_id_generator(letter_count: int = 8, digit_count: int = 4) -> str:
    """
    :param letter_count: Count of random letter
    :param digit_count: Count of random number
    :return: Unique sequence name
    """
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(letter_count))) + '-'
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count))) + '-'
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count))) + '-'
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count))) + '-'
    str1 += ''.join((random.choice(string.ascii_letters) for x in range(letter_count)))
    sam_list = list(str1)
    final_string = ''.join(sam_list)
    return final_string

def gps_file_reader(gps_file_path: str) -> tuple:
    """
    :param gps_file_path: The csv file that obtain gps values
    :return: Latitude, longitude and time values as type list
    """

    with open(gps_file_path) as csv_file:
        csv_reader = pd.read_csv(csv_file, delimiter=',')
        lats = csv_reader['lat'].tolist()
        lons = csv_reader['lon'].tolist()
        times = csv_reader['captureTime'].tolist()
    return lats, lons, times

def geojson_add_feature(lat: float, lon: float, time: str, order: float, color: str, heading: float) -> dict:
    """
    :param lat: Latitude value of  object location
    :param lon: Longitude value of  object location
    :param time: The capture time
    :param order: Order of images
    :param color: Color of object location marker
    :param heading: Heading value
    :return: Write features
    """

    return {
        "type": "Feature",
        "properties": {
            "time": time,
            "order": order,
            "marker-color": color,
            "heading": heading
        },
        "geometry": {
            "type": "Point",
            "coordinates": [
                lon,
                lat
            ]
        }
    }

def geojson_type(feature: list) -> dict:
    """
    :param feature: Features of geojson file
    :return: Convert geojson file
    """
    return {
        "type": "FeatureCollection",
        "features": feature
    }


def save_(geoFormat: dict, exportPath: str):
    """
    :param geoFormat: feature collection format
    :param exportPath: Directory of output file
    :return: Saved file
    """
    with open(exportPath, "w") as outfile:
        json.dump(geoFormat, outfile, indent=4, ensure_ascii=False)



def save_format(DataFormat, CsvFormat):

    """
    lat: str, lon: str, capture_time: str, altitude: int, roll: float, pitch: float, heading: float,
    sequenceUuid: str, orientation: int, DeviceMake: str,DeviceMode: str, ImageSize: str, FoV: int,
    PhotoUUID: str, filename: str, path: str, output_fie_name: str
    """

    data = [[DataFormat.latitude, DataFormat.longitude,
             DataFormat.captureTime, DataFormat.altitude,
             DataFormat.roll, DataFormat.pitch, DataFormat.yaw, DataFormat.heading,
             DataFormat.sequenceUuid, DataFormat.orientation, DataFormat.deviceMake,
             DataFormat.deviceModel,
             DataFormat.imageSize, DataFormat.fov,
             DataFormat.photoUuid, DataFormat.imageName, DataFormat.imagePath]]

    name = CsvFormat.OutputFileName
    with open(name, 'a', newline='') as f:
        write = csv.writer(f)
        write.writerows(data)

def save_titles(output_fie_name: str):
    """
    :param output_fie_name: Output csv file name
    :return: Write titles to csv
    """
    data = [['latitude', 'longitude', 'captureTime', 'altitude', 'roll',
             'pitch', 'yaw', 'heading', 'sequenceUuid', 'orientation',
             'deviceMake', 'deviceModel', 'imageSize', 'fov',
             'photoUuid', 'filename', 'path']]

    name = output_fie_name
    with open(name, 'a', newline='') as f:
        write = csv.writer(f)
        write.writerows(data)



class config:
    per_image_seqUID = 250


def export(csv_path, images_dir, output_geojson_name="out.geojson", output_csv_name="out.csv"):

    """
    Terminal Open, input Csv columns name
    Template Csv column first column


    :param csv_path:
    :param images_dir:
    :param output_geojson_name:
    :param output_csv_name:
    :return:
    """

    lats, lons, times = gps_file_reader(csv_path)

    capture_images = [elem for elem in sorted(os.listdir(images_dir)) if (elem.split(".")[-1]).lower() in ["jpg", "png", "jpeg"]]
    save_titles(output_csv_name)
    features_geo: list = []

    sequenceUuid = unique_sequence_id_generator(letter_count=8, digit_count=4)
    for index, img_path in enumerate(capture_images):

        image_name = os.path.basename(img_path)

        photo_uuid = photo_uuid_creater(times[index], image_name)

        if index == int(len(capture_images)) - 1:
            lats[index - 1], lons[index - 1], \
            lats[index], lons[index] = float(lats[index - 1]), float(lons[index - 1]), \
                                       float(lats[index]), float(lons[index])

            heading_cal = Distance.bearing(startLat=lats[index - 1],
                                           startLon=lons[index - 1],
                                           destLat=lats[index],
                                           destLon=lons[index])

        else:
            lats[index], lons[index], \
            lats[index + 1], lons[index + 1] = float(lats[index]), float(lons[index]),\
                                               float(lats[index + 1]), float(lons[index + 1])

            heading_cal = Distance.bearing(startLat=lats[index],
                                           startLon=lons[index],
                                           destLat=lats[index + 1],
                                           destLon=lons[index + 1])

        heading_cal = (heading_cal + 360) % 360
        if index % config.per_image_seqUID == 0:
            sequenceUuid = unique_sequence_id_generator(letter_count=8, digit_count=4)
        """Save Format Setting"""
        DataFormat.latitude = lats[index]
        DataFormat.longitude = lons[index]
        DataFormat.captureTime = times[index]
        DataFormat.altitude = 0
        DataFormat.roll = 0
        DataFormat.pitch = 0
        DataFormat.yaw = 0
        DataFormat.heading = heading_cal
        DataFormat.sequenceUuid = sequenceUuid
        DataFormat.orientation = 1
        DataFormat.photoUuid = photo_uuid
        DataFormat.imageName = image_name
        DataFormat.imagePath = ''
        CsvFormat.OutputFileName = output_csv_name
        save_format(DataFormat, CsvFormat)

        features_geo.append(geojson_add_feature(lat=float(DataFormat.latitude),
                                                lon=float(DataFormat.longitude),
                                                time=DataFormat.captureTime,
                                                order=index, color='0414fb',
                                                heading=DataFormat.heading))

    geoFormat = geojson_type(features_geo)
    geoExportPath = output_geojson_name + ".geojson"
    save_(geoFormat, geoExportPath)


