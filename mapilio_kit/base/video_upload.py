import argparse

class VideoUpload:
    name = "video_upload"
    help = "sample video into images, process the images and upload to Mapilio"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        from . import loader, sampler
        sampler().fundamental_arguments(parser)
        loader().fundamental_arguments(parser)

    def perform_task(self, vars_args: dict):
        from . import loader,sampler

        if not vars_args['processed']:
            sampler().perform_task(vars_args)
        else:
            vars_args["import_path"]=vars_args["video_import_path"]
        loader().perform_task(vars_args)
