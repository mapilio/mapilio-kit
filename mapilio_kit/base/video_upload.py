class VideoUpload:
    name = "video_upload"
    help = "sample video into images, process the images and upload to Mapilio"

    def fundamental_arguments(self, parser):
        from . import loader, sampler
        sampler().fundamental_arguments(parser)
        loader().fundamental_arguments(parser)

    def perform_task(self, vars_args: dict):
        if not vars_args['processed']:
            from . import loader, sampler
            print("Processing video")
            sampler().perform_task(vars_args)
        loader().perform_task(vars_args)
