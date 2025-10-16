import os
from pathlib import Path
from .collections import SMessage
#====================================================================

class Filesize:


    async def get01(flocation):
        try:
            moonus = os.path.getsize(flocation)
            return SMessage(filesize=moonus)
        except FileNotFoundError as errors:
            return SMessage(errors=errors)
        except PermissionError as errors:
            return SMessage(errors=errors)
        except Exception as errors:
            return SMessage(errors=errors)

#====================================================================

    async def get02(flocation):
        try:
            moones = Path(flocation)
            moonus = moones.stat().st_size
            return SMessage(filesize=moonus)
        except FileNotFoundError as errors:
            return SMessage(errors=errors)
        except PermissionError as errors:
            return SMessage(errors=errors)
        except Exception as errors:
            return SMessage(errors=errors)

#====================================================================

    async def get21(allfiles, size=0):
        for file in allfiles:
            raws = await Filesize.get02(file)
            size += raws.filesize

        return SMessage(filesize=size)

#====================================================================
