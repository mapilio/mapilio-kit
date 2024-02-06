import csv
import json
import os.path


def process_csv_to_description(
        csv_path: str,
        import_path: str,
        processed: bool = False,
) -> None:
    """

    Args:
        csv_path: read image description csv format
        import_path: read image directory

    Returns:
        convert default description format and save under the import_path directory
    """

    with open(csv_path) as f:
        float_columns = ['latitude', 'longitude', 'heading', 'fov', 'yaw', 'megapixels', 'carSpeed',
                         'roll', 'pitch', 'altitude', 'orientation']
        mapilio_description = [
            {
                k: float(v) if k in float_columns and v.replace('.', '').isdigit() else v for k, v in row.items()
            } for row in csv.DictReader(f, skipinitialspace=True)]

        [data.update({"source": "Mapilio_Kit"}) for data in mapilio_description]

        processed = len(mapilio_description)
        description_information = {
            "Information": {
                "total_images": processed,
                "processed_images": processed,
                "failed_images": 0,
                "duplicated_images": 0,
                "id": "8323ff0a01fe49d1b55e610279f62828",
                "device_type": "Desktop"
            }
        }
        mapilio_description.append(description_information)

    save_path = os.path.join(import_path, 'mapilio_image_description.json')
    with open(save_path, 'w') as outfile:
        json.dump(mapilio_description, outfile)
