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
        from . import decomposer
        self.authenticator = authenticator()
        self.uploader = uploader()
        self.video_loader = video_loader()
        self.decomposer = decomposer()
        self.video_sample_interval = 1
        self.interpolate_directions = True

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
        args = self.get_args(edit_config)
        import_path = input("Enter your image path: ").strip()

        if import_path:
            args["import_path"] = import_path
            return self.decomposer.perform_task(args)
        else:
            print("Please enter your image path and processed properly \n\n\n\n\n")
            self.perform_image_upload()

    def perform_video_upload(self):
        args = self.get_args(upload)
        video_import_path = input("Enter your video path: ").strip()
        processed = input("Are your images processed [y,Y,yes,Yes]?").strip()
        if video_import_path:
            import_path = '/'.join(video_import_path.split('/')[:-1]) + '/' + 'images' + '/'
            print(import_path)
            args["import_path"] = import_path
            if processed not in ["y", "Y", "yes", "Yes"]:
                args["video_import_path"] = video_import_path
                geotag_source = input(
                    "Enter your geotag source (choices=['exif', 'gpx', 'gopro_videos', 'nmea']): ").strip()
                # self.video_sample_interval = int(input("Enter your video sample interval: ").strip())
                args["processed"] = False
                args["geotag_source"] = geotag_source
                args["interpolate_directions"] = self.interpolate_directions
                args["video_sample_interval"] = self.video_sample_interval
                return self.video_loader.perform_task(args)


            else:
                # desc_path = input("Enter your description json path: ").strip()
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
                if advanced_func == "5.1" or advanced_func == "Decompose":
                    self.perform_decompose()
                if advanced_func == "5.2" or advanced_func == "360-panorama-image-upload":
                    pass
                if advanced_func == "5.3" or advanced_func == "Zip-upload":
                    pass
                elif advanced_func == "q":
                    exit()
            elif func == "q":
                exit()
            else:
                print("\n\nPlease enter a valid option\n\n")
                Run().perform_task(vars_args=None)

if __name__ == "__main__":
    print("Welcome to Mapilio-kit\n")
    Run().perform_task(vars_args=None)
