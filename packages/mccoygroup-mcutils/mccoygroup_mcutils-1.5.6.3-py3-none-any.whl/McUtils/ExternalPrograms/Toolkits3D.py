
import io
import base64
from .Interface import *

__all__ = [
    "Open3DInterface",
]

class Open3DInterface(ExternalProgramInterface):
    """
    A simple class to support operations that make use of the OpenCV toolkit
    """
    name = 'Open3D'
    module = 'open3d'