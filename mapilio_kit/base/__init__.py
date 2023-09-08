from .upload import Upload
from .decompose import Decompose
from .authenticate import Authenticate
from .sampler import Sampler
from .video_upload import VideoUpload
from .image_and_csv_upload import image_and_csv_upload
from .process_csv import CSVprocess

CSVprocesser = CSVprocess
image_and_csv_uploader = image_and_csv_upload
loader = Upload
decomposer = Decompose
authenticator = Authenticate
sampler = Sampler
video_loader = VideoUpload
