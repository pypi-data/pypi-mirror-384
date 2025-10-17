"""
Provides support for chemical toolkits
"""
import io
import base64
from .Interface import *

__all__ = [
    "PILInterface",
    "OpenCVInterface"
]

class PILInterface(ExternalProgramInterface):
    """
    A simple class to support operations that make use of the OpenCV toolkit
    """
    name = 'PIL'
    module = 'PIL'
    @classmethod
    def from_file(cls, file, **opts):
        return cls.method("Image").open(file, **opts)

    @classmethod
    def from_url(cls, url):
        format, buf = cls.prep_url_buffer(url)
        if format is None:
            format = 'png'
        return cls.method('Image').open(buf)#, format=format)

    @classmethod
    def to_url(cls, image, format='png'):
        buf = io.BytesIO()
        image.save(buf, format=format)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    @classmethod
    def prep_url_buffer(cls, img_data: str, format=None):
        if img_data.startswith('data:image/'):
            tag, img_data = img_data.split(";", 1)
            if format is None:
                format = tag.split("/")[1]

        b64_tag = 'base64,'
        if img_data.startswith(b64_tag):
            return format, io.BytesIO(base64.b64decode(img_data[len(b64_tag):]))
        else:
            return format, io.BytesIO(img_data.encode('ascii'))


class OpenCVInterface(ExternalProgramInterface):
    """
    A simple class to support operations that make use of the PIL toolkit
    """
    name = 'OpenCV'
    module = 'cv2'