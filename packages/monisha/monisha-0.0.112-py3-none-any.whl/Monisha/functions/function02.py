from ..scripts import Humon, Scripted
#=============================================================================

def Dbytes(sizes, second=Scripted.DATA01):
    if not sizes or sizes == Scripted.DATA02:
        return Scripted.DATA09 + second
    elif str(sizes) < str(0):
        return Scripted.DATA09 + second
    nomos = 0
    POWEO = 1024
    sized = int(sizes)
    POWER = Humon.DATA01
    while sized > POWEO:
        sized /= POWEO
        nomos += 1
    return str(round(sized, 2)) + Scripted.DATA02 + POWER[nomos] + second

#=============================================================================

def Hbytes(sizes, second=Scripted.DATA01):
    if not sizes or sizes == Scripted.DATA02:
        return Scripted.DATA08 + second
    elif str(sizes) < str(0):
        return Scripted.DATA08 + second
    nomos = 0
    POWEO = 1024
    sized = int(sizes)
    POWER = Humon.DATA02
    while sized > POWEO:
        sized /= POWEO
        nomos += 1
    return str(round(sized, 2)) + Scripted.DATA02 + POWER[nomos] + second

#=============================================================================

def Gbytes(sizes, second=Scripted.DATA01):
    if not sizes or sizes == Scripted.DATA02:
        return Scripted.DATA01 + second
    elif str(sizes) < str(0):
        return Scripted.DATA01 + second
    nomos = 0
    POWEO = 1024
    sized = int(sizes)
    POWER = Humon.DATA01
    while sized > POWEO:
        sized /= POWEO
        nomos += 1
    return str(round(sized, 2)) + Scripted.DATA02 + POWER[nomos] + second

#=============================================================================
