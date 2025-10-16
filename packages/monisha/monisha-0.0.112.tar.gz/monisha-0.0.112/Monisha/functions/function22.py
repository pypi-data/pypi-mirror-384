import os
import time
from PIL import Image
from ..scripts import Scripted
from .collections import SMessage
#===========================================================================

class Thumbnail:

    def get01(flocation):
        try:
            image = Image.open(flocation)
            image = image if image.mode == "RGB" else image.convert("RGB")
            moonu = Scripted.DATA18.format(round(time.time()))
            image.save(moonu, "JPEG")
            os.remove(flocation)
            return SMessage(thumbnail=moonu)
        except Exception as errors:
            return SMessage(thumbnail=flocation, errors=errors)

#===========================================================================

    async def get02(flocation):
        try:
            image = Image.open(flocation)
            image = image if image.mode == "RGB" else image.convert("RGB")
            moonu = Scripted.DATA18.format(round(time.time()))
            image.save(moonu, "JPEG")
            os.remove(flocation)
            return SMessage(thumbnail=moonu)
        except Exception as errors:
            return SMessage(thumbnail=flocation, errors=errors)

#===========================================================================
