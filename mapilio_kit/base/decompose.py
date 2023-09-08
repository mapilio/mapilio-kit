import argparse
from insert_MAPJson import insert_MAPJson
from geotag_property_handler import geotag_property_handler
from metadata_property_handler import metadata_property_handler
from sequence_property_handler import sequence_property_handler


class Decompose():
    name = "decompose"
    help = "Decompose images"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--skip_decompose_errors",
            help="Skip decompose errors.",
            action="store_true",
            default=True,
            required=False,
        )
        group = parser.add_argument_group("Decompose EXIF options")
        group.add_argument(
            "--overwrite_all_EXIF_tags",
            help="Overwrite the rest of the EXIF tags, whose values are changed during the decomposing. Default is False"
                 ", which will result in the decomposed values to be inserted only in the EXIF Image Description tag.",
            action="store_true",
            default=False,
            required=False,
        )
        group.add_argument(
            "--overwrite_EXIF_time_tag",
            help="Overwrite the capture time EXIF tag with the value obtained in decompose.",
            action="store_true",
            default=False,
            required=False,
        )
        group.add_argument(
            "--overwrite_EXIF_gps_tag",
            help="Overwrite the GPS EXIF tag with the value obtained in decompose.",
            action="store_true",
            default=False,
            required=False,
        )
        group.add_argument(
            "--overwrite_EXIF_direction_tag",
            help="Overwrite the camera direction EXIF tag with the value obtained in decompose.",
            action="store_true",
            default=False,
            required=False,
        )
        group.add_argument(
            "--overwrite_EXIF_orientation_tag",
            help="Overwrite the orientation EXIF tag with the value obtained in decompose.",
            action="store_true",
            default=False,
            required=False,
        )

        group_metadata = parser.add_argument_group("decompose metadata options")
        group_metadata.add_argument(
            "--device_make",
            help="Specify device manufacturer. Note this input has precedence over the input read from "
                 "the import source file.",
            default=None,
            required=False,
        )
        group_metadata.add_argument(
            "--device_model",
            help="Specify device model. Note this input has precedence over the input read from"
                 " the import source file.",
            default=None,
            required=False,
        )
        group_metadata.add_argument(
            "--add_file_name",
            help="Add original file name to EXIF. Note this input has precedence over the input read from the "
                 "import source file.",
            action="store_true",
            required=False,
        )
        group_metadata.add_argument(
            "--exclude_import_path",
            help="If local file name is to be added exclude import_path from the name.",
            action="store_true",
            required=False,
        )
        group_metadata.add_argument(
            "--exclude_path",
            help="If local file name is to be added, specify the path to be excluded.",
            default=None,
            required=False,
        )
        group_metadata.add_argument(
            "--add_import_date",
            help="Add import date.",
            action="store_true",
            required=False,
        )
        group_metadata.add_argument(
            "--windows_path",
            help="If local file name is to be added with --add_file_name, added it as a windows path.",
            action="store_true",
            required=False,
        )
        group_metadata.add_argument(
            "--orientation",
            help="Specify the image orientation in degrees. Note this might result in image rotation. "
                 "Note this input has precedence over the input read from the import source file.",
            choices=[0, 90, 180, 270],
            type=int,
            default=None,
            required=False,
        )
        group_metadata.add_argument(
            "--GPS_accuracy",
            help="GPS accuracy in meters. Note this input has precedence over the input read from "
                 "the import source file.",
            default=None,
            required=False,
        )
        group_metadata.add_argument(
            "--camera_uuid",
            help="Custom string used to differentiate different captures taken with the same camera make and model.",
            default=None,
            required=False,
        )
        group_metadata.add_argument(
            "--custom_meta_data",
            help='Add custom meta data to all images. Required format of input is a string, consisting of '
                 'the meta data name, type and value, separated by a comma for each entry, where entries are '
                 'separated by semicolon. Supported types are long, double, string, boolean, date. '
                 'Example for two meta data entries "random_name1,double,12.34;random_name2,long,1234"',
            default=None,
            required=False,
        )

        group_geotagging = parser.add_argument_group("decompose geotagging options")
        group_geotagging.add_argument(
            "--desc_path",
            help="Specify the path to store mapilio image descriptions as JSON. By default it is "
                 "{IMPORT_PATH}/mapilio_image_description.json",
            default=None,
            required=False,
        )
        group_geotagging.add_argument(
            "--geotag_source",
            help="Provide the source of date/time and GPS information needed for geotagging",
            action="store",
            choices=["exif", "gpx", "gopro_videos", "nmea"],
            default="exif",
            required=False,
        )
        group_geotagging.add_argument(
            "--geotag_source_path",
            help="Provide the path to the file source of date/time and GPS information needed for geotagging",
            action="store",
            default=None,
            required=False,
        )
        group_geotagging.add_argument(
            "--offset_time",
            default=0.0,
            type=float,
            help="time offset, in seconds, that will be added to your image timestamps",
            required=False,
        )
        group_geotagging.add_argument(
            "--offset_angle",
            default=0.0,
            type=float,
            help="camera angle offset, in degrees, that will be added to your image camera angles",
            required=False,
        )

        group_sequence = parser.add_argument_group("decompose sequence options")
        group_sequence.add_argument(
            "--cutoff_distance",
            default=600.0,
            type=float,
            help="maximum GPS distance in meters within a sequence",
            required=False,
        )
        group_sequence.add_argument(
            "--cutoff_time",
            default=60.0,
            type=float,
            help="maximum time interval in seconds within a sequence",
            required=False,
        )
        group_sequence.add_argument(
            "--interpolate_directions",
            help="perform interploation of directions",
            action="store_true",
            required=False,
        )
        group_sequence.add_argument(
            "--duplicate_angle",
            help="max angle for two images to be considered duplicates in degrees",
            type=float,
            default=5,
            required=False,
        )

    def filter_args(self, func, args):
        return {k: v for k, v in args.items() if k in func.__code__.co_varnames}

    def perform_task(self, vars_args: dict):
        metadata_property_handler_args = self.filter_args(metadata_property_handler, vars_args)
        metadata_property_handler(**metadata_property_handler_args)

        geotag_property_handler_args = self.filter_args(geotag_property_handler, vars_args)
        geotag_property_handler(**geotag_property_handler_args)

        sequence_property_handler_args = self.filter_args(sequence_property_handler, vars_args)
        sequence_property_handler(**sequence_property_handler_args)

        insert_MAPJson_args = self.filter_args(insert_MAPJson, vars_args)
        insert_MAPJson(**insert_MAPJson_args)
