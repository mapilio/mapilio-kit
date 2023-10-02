import os
import getpass
import subprocess
from login import list_all_users
from upload import upload, zip_images
from edit_config import edit_config
from process_csv_to_description import process_csv_to_description


class Run:
    name = "run"
    help = "Follow instructions of magic usage of Mapilio-kit."

    def __init__(self):
        from . import authenticator
        from . import uploader
        from . import video_loader
        from . import decomposer
        from . import image_and_csv_uploader
        from . import Zipper
        self.authenticator = authenticator()
        self.uploader = uploader()
        self.video_loader = video_loader()
        self.decomposer = decomposer()
        self.image_and_csv_uploader = image_and_csv_uploader()
        self.zipper = Zipper()
        self.video_sample_interval = 1
        self.interpolate_directions = True
        self.username = None

    def fundamental_arguments(self, parser):
        group = parser.add_argument_group("run options")

    def check_auth(self):
        print("Please enter your Mapilio account information to continue.\n"
              "If you don't have a Mapilio account, please create one at https://mapilio.com/ \n")
        user_name = input("Enter your username: ").strip()
        user_email = input("Enter your email: ").strip()
        user_password = getpass.getpass("Enter Mapilio user password: ").strip()

        if user_name and user_email and user_password:
            args = self.get_args(edit_config)
            args["user_name"] = user_name
            args["user_email"] = user_email
            args["user_password"] = user_password
            check_authenticate = self.authenticator.perform_task(args)
            if check_authenticate:
                return check_authenticate
            else:
                self.check_auth()

        else:
            print("Please enter your username, email and password properly \n\n\n\n\n")
            self.check_auth()

    def perform_image_upload(self):
        try:
            result = subprocess.run(['exiftool', '-ver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            print("Please install exiftool\n\n\n\n\n")
            exit()
        args = self.get_args(upload)
        args["user_name"] = self.username
        import_path = input("Enter your image path: ").strip()
        processed = input(
            "Are your images processed already [y,Y,yes,Yes]? (Hint: will convert your images to exif data and write them to a json file):").strip()

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

    def panorama_image_upload(self):
        args = self.get_args(process_csv_to_description)
        import_path = input("Enter your image path: ").strip()
        csv_path = input("Enter your csv path: ").strip()

        if import_path and csv_path:
            args["import_path"] = import_path
            args["csv_path"] = csv_path
            args["processed"] = False

            return self.image_and_csv_uploader.perform_task(args)

        else:
            print("Please enter your image and csv path properly \n\n\n\n\n")
            self.panorama_image_upload()

    def perform_decompose(self):
        args = self.get_args(edit_config)
        import_path = input("Enter your image path: ").strip()

        if import_path:
            args["import_path"] = import_path
            return self.decomposer.perform_task(args)
        else:
            print("Please enter your image path properly \n\n\n\n\n")
            self.perform_decompose()

    def perform_video_upload(self):
        try:
            result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            print("Please install ffmpeg\n\n\n\n\n")
            exit()
        args = self.get_args(upload)
        args["user_name"] = self.username
        video_import_path = input("Enter your video folder path: ").strip()
        processed = input("Are your images processed already [y,Y,yes,Yes]?").strip()
        if video_import_path:
            import_path = '/'.join(video_import_path.split('/')[:-1]) + '/' + 'images' + '/'
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
            print("Please enter your video path properly \n\n\n\n\n")
            self.perform_video_upload()

    def gopro360max_upload(self):
        pass

    def zip_upload(self):
        args = self.get_args(zip_images)
        import_path = input("Enter your image path: ").strip()
        zip_dir = import_path
        if import_path:
            args["import_path"] = import_path
            args["zip_dir"] = zip_dir
            args["processed"] = False
            check_zip = self.zipper.perform_task(args)
            if check_zip:
                zip_file_path = \
                    [os.path.join(zip_dir, filename) for filename in os.listdir(zip_dir) if filename.endswith(".zip")][
                        0]
                args["processed"] = True
                args["import_path"] = zip_file_path
                self.uploader.perform_task(args)

        else:
            print("Please enter your image path properly \n\n\n\n\n")
            self.zip_upload()

    def get_args(self, func):
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        return {arg: None for arg in arg_names}

    def perform_task(self, vars_args: dict):
        if vars_args is not None:
            print("Welcome to Mapilio-kit\n"
                  "Mapilio allows you to upload your images, videos and 360 degree panorama images to Mapilio map.\n")

        if len(list_all_users()) == 0:
            check_authenticate = self.check_auth()
        elif len(list_all_users()) >= 2:
            self.username = input("Found multiple Mapilio accounts. Please specify your username.\n")
        else:
            check_authenticate = True

        if check_authenticate:
            func = input("Choose your process:\n\
                         1. Image upload (Hint: Basically, Image Upload takes your images or timelapse images, processes and uploads them to Mapilio.)\n\
                         2. Video upload (Hint: Briefly, Video Upload takes your video or panoramic video that obtained from gopro360max, processes it (as 1 second timelapse photos) and uploads to Mapilio.)\n\
                         3. Advanced options (Hint: This option gives access to more advanced processing options.)\n"
                         )

            if func == "1" or func == "Image upload":
                self.perform_image_upload()

            elif func == "2" or func == "Video upload":
                video_func = input("Choose your video process:\n\
                             1. Video upload (Hint: Briefly, Video Upload takes your video, processes it (as 1 second timelapse photos) and uploads to Mapilio.)\n\
                             2. gopro360max panoramic video upload (Hint: Takes your panoramic images, processes and uploads to Mapilio.) still in progress!\n"
                                   )
                if video_func == "1" or video_func == "Video upload":
                    self.perform_video_upload()
                elif video_func == "2" or video_func == "gopro360max panoramic video upload":
                    self.gopro360max_upload()
                elif video_func == "q":
                    exit()
                else:
                    print("\n\nYou've entered an invalid option. Please enter a valid option\n\n")
                    Run().perform_task(vars_args=None)
            elif func == "3" or func == "Advance options":
                advanced_func = input("Choose your advanced process:\n\
                                         1 Decompose (Hint: Shortly, Decompose extracts metadata information to json file from images by using EXIF Tool.)\n\
                                         2 360 panorama image upload (Hint: In Short, 360 panorama image upload takes 360 degree panorama images with their csv file which taken from surveying car and then uploads to Mapilio.)\n"
                                      )
                if advanced_func == "1" or advanced_func == "Decompose":
                    self.perform_decompose()
                if advanced_func == "2" or advanced_func == "360 panorama image upload":
                    self.panorama_image_upload()
                elif advanced_func == "q":
                    exit()
                else:
                    print("\n\nYou've entered an invalid option. Please enter a valid option\n\n")
                    Run().perform_task(vars_args=None)

            elif func == "q":
                exit()
            else:
                print("\n\nYou've entered an invalid option. Please enter a valid option\n\n")
                Run().perform_task(vars_args=None)


if __name__ == "__main__":
    Run().perform_task(vars_args=None)
