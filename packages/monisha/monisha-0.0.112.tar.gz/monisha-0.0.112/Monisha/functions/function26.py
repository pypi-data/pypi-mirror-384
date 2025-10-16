import re
from ..scripts import Scripted
from ..scripts import Unicodes
#======================================================================

class Cleans:

    def clean01(incoming):
        moonus = re.compile(Unicodes.DATA01, flags=re.UNICODE)
        return moonus.sub(r'', str(incoming))

#======================================================================

    def clean02(texted, keys=None, none=Scripted.DATA01):
        if not keys:
            return texted
        return none.join(keys.get(chao, chao) for chao in texted)

#======================================================================
