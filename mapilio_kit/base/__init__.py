from mapilio_kit.base.loader import Upload
from mapilio_kit.base.decompose import Decompose
from mapilio_kit.base.authenticate import Authenticate
from mapilio_kit.base.sampler import Sampler
from mapilio_kit.base.video_upload import VideoUpload
from mapilio_kit.base.image_and_csv_upload import image_and_csv_upload
from mapilio_kit.base.process_csv import CSVprocess
from mapilio_kit.base.gopro_360max import gopro360max_process
from mapilio_kit.base.zip import Zip
from mapilio_kit.base.run import Run

Zipper = Zip
gopro360max_processor = gopro360max_process
CSVprocessor = CSVprocess
image_and_csv_uploader = image_and_csv_upload
uploader = Upload
decomposer = Decompose
authenticator = Authenticate
sampler = Sampler
video_loader = VideoUpload
run_mapi = Run
