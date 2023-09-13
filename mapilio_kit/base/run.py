import sys
import os
import getpass

sys.path.append(os.getcwd() + r"/mapilio_kit/components")
from upload import upload
from edit_config import edit_config


class Run:
    name = "run"
    # TODO: change help
    help = "Mapilio"

    def __init__(self):
        from . import authenticator
        from . import uploader
        from . import video_loader
        self.authenticator = authenticator()
        self.uploader = uploader()
        self.video_loader = video_loader()

    def fundamental_arguments(self, parser):
        group = parser.add_argument_group("run options")

    def check_auth(self):
        user_name = input("Enter your username: ").strip()
        user_email = input("Enter your email: ").strip()
        user_password = getpass.getpass("Enter Mapilio user password: ").strip()

        if user_name and user_email and user_password:
            args = self.get_args(edit_config)
            args["user_name"] = user_name
            args["user_email"] = user_email
            args["user_password"] = user_password
            return self.authenticator.perform_task(args)

        else:
            print("Please enter your username, email and password properly \n\n\n\n\n")
            self.check_auth()

    def perform_image_upload(self):
        args = self.get_args(upload)
        import_path = input("Enter your image path: ").strip()
        processed = input("Are your images processed [y,Y,yes,Yes]?").strip()


        if import_path and processed:
            args["import_path"] = import_path

            if processed not in ["y", "Y", "yes", "Yes"]:
                args["processed"] = False
            else:
                args["processed"] = True

            return self.uploader.perform_task(args)

        else:
            print("Please enter your image path and processed properly \n\n\n\n\n")
            self.perform_image_upload()

    def perform_decompose(self):
        pass

    def perform_video_upload(self):
        args = self.get_args(upload)
        video_import_path = input("Enter your video path: ").strip()
        processed = input("Are your images processed [y,Y,yes,Yes]?").strip()
        if video_import_path:
            import_path = input("Enter your sample images path: ").strip()
            args["import_path"] = import_path
            if processed not in ["y", "Y", "yes", "Yes"]:
                args["video_import_path"] = video_import_path
                geotag_source = input(
                    "Enter your geotag source (choices=['exif', 'gpx', 'gopro_videos', 'nmea']): ").strip()
                interpolate_directions = True
                video_sample_interval = int(input("Enter your video sample interval: ").strip())
                args["processed"] = False
                args["geotag_source"] = geotag_source
                args["interpolate_directions"] = interpolate_directions
                args["video_sample_interval"] = video_sample_interval
                return self.video_loader.perform_task(args)


            else:
                desc_path = input("Enter your description json path: ").strip()
                # args["desc_path"] = desc_path
                args["processed"] = True
                return self.uploader.perform_task(args)


        else:
            print("Please enter your image path and processed properly \n\n\n\n\n")
            self.perform_video_upload()


    def gopro360max_upload(self):
        pass

    def get_args(self, func):
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        return {arg: None for arg in arg_names}

    def perform_task(self, vars_args: dict):
        # if self.check_auth():
        if True:
            func = input("Choose your process:\n\
                         1. image-upload \n\
                         2. timelapse-upload\n\
                         3. Video-Upload\n\
                         4. gopro360max-upload\n\
                         5. Advance options\n"
                         )

            if func == "1" or func == "image-upload" or func == "2" or func == "timelapse-upload":
                self.perform_image_upload()

            elif func == "3" or func == "Video-Upload":
                self.perform_video_upload()

            elif func == "4" or func == "gopro360max-upload":
                self.gopro360max_upload()

            elif func == "5" or func == "image-and-csv-upload":
                advanced_func = input("Choose your advanced process:\n\
                                         5.1 Decompose \n\
                                         5.2 360-panorama-image-upload\n\
                                         5.3 Zip-upload\n"
                                      )
                if advanced_func == "q":
                    exit()
            elif func == "q":
                exit()
            else:
                print("\n\nPlease enter a valid option\n\n")
                Run().perform_task(vars_args=None)

import configparser

def load_config(config_path: str) -> configparser.ConfigParser:
    if not os.path.isfile(config_path):
        raise RuntimeError(f"config {config_path} does not exist")
    config = configparser.ConfigParser()
    config.optionxform = str  # type: ignore
    config.read(config_path)
    return config


def save_config(config: configparser.ConfigParser, config_path: str) -> None:

    with open(config_path, "w") as cfg:
        print(cfg)
        config.write(cfg)

def delete_user(config: configparser.ConfigParser, user_name: str, config_path: str) -> None:
    print(config.sections())

    if user_name in config.sections():
        config.remove_section(user_name)
        save_config(config, config_path)
    else:
        print(f"Error, user {user_name} does not exist")
MAPILIO_CONFIG_PATH = os.getenv(
    "MAPILIO_CONFIG_PATH",
    os.path.join(
        os.path.expanduser("~"),
        ".config",
        "mapilio",
        "configs",
        "CLIENT_USERS",
    ),
)
if __name__ == "__main__":
    print("Welcome to Mapilio-kit\n")
    Run().perform_task(vars_args=None)

    # global_config_object = load_config(MAPILIO_CONFIG_PATH)
    # user_name = "omer_faruk_karaboga"
    # delete_user(global_config_object, user_name, MAPILIO_CONFIG_PATH)

