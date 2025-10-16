import asyncio
from asyncio.subprocess import PIPE
from .collections import SMessage
#======================================================================================

async def commandR(command, **kwargs):
    try:
        mainos = await asyncio.create_subprocess_exec(*command,
        stdout=PIPE, stderr=PIPE, **kwargs) 
        moonus = await mainos.communicate()
        resues = moonus[0]
        errose = moonus[1]
        codeos = mainos.returncode
        result = resues.decode("utf-8", errors="ignore").strip()
        errors = errose.decode("utf-8", errors="ignore").strip()
        return SMessage(results=result, taskcode=codeos, errors=errors)
    except Exception as errors:
        return SMessage(errors=errors)

#======================================================================================
