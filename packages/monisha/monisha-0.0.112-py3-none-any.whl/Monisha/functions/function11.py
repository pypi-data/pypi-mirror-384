from ..scripts import Scripted
#============================================================================

async def con2s(recived):
    messae = Scripted.DATA01.join("{}, ".format(elem) for elem in recived)
    moones = messae.rsplit(", ", 1)
    moonus = Scripted.DATA01.join(moones)
    return moonus

#============================================================================
