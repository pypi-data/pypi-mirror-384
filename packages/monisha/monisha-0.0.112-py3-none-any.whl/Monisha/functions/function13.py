import random
from .function06 import Skeys
from ..scripts import Scripted
#=======================================================================================

async def Randoms(length=32, message=Skeys.DATA04):
    raumes = random.randint(10, length)
    ouoing = Scripted.DATA01.join(random.choice(message) for _ in range(raumes))
    return ouoing

#=======================================================================================
