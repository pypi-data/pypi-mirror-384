from ..scripts import Numeo
from decimal import Decimal, ROUND_DOWN
#==================================================================================

def views(sizes):
    si = str(sizes)
    if not si.isdigit() or si == str(0) or si < str(0):
        return sizes
    indeu = 0
    power = 1000
    sizes = int(si)
    while sizes >= power and indeu < len(Numeo.DATA01) - 1:
        sizes /= power
        indeu += 1
    sized = float(Decimal(sizes).quantize(Decimal('0.01'), rounding=ROUND_DOWN))
    sizeo = str(int(sized)) if sized.is_integer() else str(round(sized, 2))
    moonu = sizeo + Numeo.DATA01[indeu]
    return moonu

#==================================================================================
