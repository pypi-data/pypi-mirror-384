import os
import time
import shutil
from pathlib import Path
from .function04 import Eimes
from ..scripts import Folders
from ..scripts import Scripted
from .collections import SMessage
#================================================================================

class Location:

    async def mak00(name=Folders.DATA07):
        direos = str(name)
        osemse = os.getcwd()
        moonse = os.path.join(osemse, direos, Scripted.DATA01)
        shutil.rmtree(moonse) if os.path.isdir(moonse) else moonse
        os.makedirs(moonse) if not os.path.isdir(moonse) else moonse

#================================================================================
    
    async def mak01(name=Folders.DATA07):
        direos = str(name)
        osemse = os.getcwd()
        moonse = os.path.join(osemse, direos, Scripted.DATA01)
        moonse if os.path.exists(moonse) else os.makedirs(moonse)
        return moonse

#================================================================================

    async def mak02(name=Folders.DATA07):
        direos = str(name)
        osemse = os.getcwd()
        timeso = str(round(time.time()))
        moonse = os.path.join(osemse, direos, timeso, Scripted.DATA01)
        moonse if os.path.exists(moonse) else os.makedirs(moonse)
        return moonse

#================================================================================

    async def mak03(uid, name=Folders.DATA07):
        usered = str(uid)
        direos = str(name)
        osemse = os.getcwd()
        timeso = str(round(time.time()))
        moonse = os.path.join(osemse, direos, usered, timeso, Scripted.DATA01)
        moonse if os.path.exists(moonse) else os.makedirs(moonse)
        return moonse

#================================================================================

    async def rem01(file):
        flocation = Path(file)
        flocation.unlink() if flocation.exists() else None
#================================================================================

    async def rem02(files):
        for file in files:
            flocation = Path(file)
            flocation.unlink() if flocation.exists() else None

#================================================================================    

    async def get01(directory, stored=None):
        sos = stored if stored else []
        for item in Path(directory).rglob('*'):
            if item.is_file():
                sos.append(str(item))

        sos.sort()
        return SMessage(allfiles=sos, numfiles=len(sos))

#================================================================================

    async def get02(directory, stored=None, skip=Eimes.DATA00):
        sos = stored if stored else []
        for patho in directory:
            if not patho.upper().endswith(skip):
                sos.append(patho)
    
        sos.sort()
        return SMessage(allfiles=sos, numfiles=len(sos))

#================================================================================

    async def get03(directory, stored=None, filter=Eimes.DATA05):
        sos = stored if stored else []
        for patho in directory:
            if patho.upper().endswith(filter):
                sos.append(patho)

        sos.sort()
        return SMessage(allfiles=sos, numfiles=len(sos))

#================================================================================
