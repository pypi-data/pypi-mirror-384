import arrow
from .function05 import Doxo
#====================================================================

class Premium(Doxo):

    async def reg01(moonus):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.shift(years=moonus)
        moones = moon02.format(Doxo.DATA05)
        return moones    

    async def reg02(moonus):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.shift(days=moonus)
        moones = moon02.format(Doxo.DATA05)
        return moones

    async def reg03(moonus):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.shift(hours=moonus)
        moones = moon02.format(Doxo.DATA05)
        return moones
    
    async def reg04(moon):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.shift(minutes=moon)
        moones = moon02.format(Doxo.DATA05)
        return moones

    async def reg05(moon):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.shift(seconds=moon)
        moones = moon02.format(Doxo.DATA05)
        return moones
    
    async def get01(moonus):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.shift(days=moonus)
        moones = moon02.format(Doxo.DATA05)
        return moones

    async def get02(moonus):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.format(Doxo.DATA05)
        moon03 = arrow.get(moon02, Doxo.DATA05)
        moon04 = arrow.get(moonus, Doxo.DATA05)
        moones = (moon04 - moon03).days
        return moones

    async def get03(moonus):
        moon01 = arrow.now("Asia/Kolkata")
        moon02 = moon01.format(Doxo.DATA05)
        moon03 = arrow.get(moon02, Doxo.DATA05)
        moon04 = arrow.get(moonus, Doxo.DATA05)
        moones = round((moon04 - moon03).total_seconds())
        return moones

#====================================================================
