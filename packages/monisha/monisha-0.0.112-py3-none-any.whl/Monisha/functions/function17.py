import os
import time
import random
from ..scripts import Scripted
from urllib.parse import unquote
from urllib.parse import urlparse
from .collections import SMessage
#=========================================================================

class Filename:

    async def get01(extension=None):
        mainos = str(random.randint(10000, 100000000000000))
        moonus = mainos + extension if extension else mainos
        return moonus

#=========================================================================

    async def get00(filename, incoming):
        nameos = str(filename)
        nameus = str(incoming)
        exeoxe = os.path.splitext(nameos)[1]
        exoexo = os.path.splitext(nameus)[1]
        moonus = exoexo if exoexo else exeoxe
        return SMessage(extension=moonus, filename=incoming)

#=========================================================================

    async def get02(filename, extension=Scripted.DATA06):
        nameas = str(filename)
        finame = os.path.splitext(nameas)[0]
        exexon = os.path.splitext(nameas)[1]
        exoexo = exexon if exexon else str(extension)
        moonus = finame if finame else Scripted.DATA13
        return SMessage(filename=moonus, extension=exoexo)

#=========================================================================

    async def get03(filelink):
        try:
            findne = urlparse(filelink)
            moonus = unquote(os.path.basename(findne.path))
            moones = moonus if moonus else Scripted.DATA14
            return SMessage(filename=moones, errors=moones)
        except Exception as errors:
            return SMessage(filename=Scripted.DATA14, errors=errors)

#=========================================================================

    async def get04(location):
        try:
            moonus = str(os.path.basename(location))
            return SMessage(filename=moonus, errors=None)
        except Exception as errors:
            return SMessage(filename=Scripted.DATA14, errors=errors)

#=========================================================================

    async def get05(location, filename=None, extension=Scripted.DATA06):
        try:
            moones = filename if filename else round(time.time())
            moonus = str(location) + str(moones) + extension
            return SMessage(filename=moonus, errors=None)
        except Exception as errors:
            return SMessage(filename=Scripted.DATA14, errors=errors)

#=========================================================================
