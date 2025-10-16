from .function29 import Extensions
from ..scripts import Scripted
#=============================================================================

class CheckExtension:

    async def get01(filename, incoming):
        if filename.lower().endswith(Extensions.DATA02):
            pass
        elif incoming.lower().endswith(Extensions.DATA02):
            pass
        else:
            raise ValueError(Scripted.ERROR01)

#=============================================================================

    async def get02(filename):
        moones = filename.lower()
        return True if moones.endswith(Extensions.DATA02) else False

#=============================================================================
