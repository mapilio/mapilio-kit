import sys
import os
pwd = os.getcwd()
sys.path.append(pwd+r"/mapilio_kit_v2/components")
from .upload import Upload
from.decompose import Decompose
from .authenticate import Authenticate

loader=Upload
decomposer=Decompose
authenticator=Authenticate