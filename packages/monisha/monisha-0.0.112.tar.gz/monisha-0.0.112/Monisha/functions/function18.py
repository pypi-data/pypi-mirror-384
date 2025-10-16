from ..scripts import Scripted
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
#=====================================================================

class Metadatas:

    async def title(flocation, default=Scripted.DATA03):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if not metadata or metadata == None:
            return default
        title = metadata.get("title", default)
        return title

#=====================================================================

    async def artist(flocation, default=Scripted.DATA03):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if not metadata or metadata == None:
            return default
        title = metadata.get("artist", default)
        return title

#=====================================================================

    async def width(flocation, default=0):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if not metadata or metadata == None:
            return default
        width = metadata.get("width", default)
        return width

#=====================================================================

    async def height(flocation, default=0):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if not metadata or metadata == None:
            return default
        height = metadata.get("height", default)
        return height

#=====================================================================

    async def duration(flocation, default=0):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if not metadata or metadata == None:
            return default
        duration = metadata.get("duration", default)
        durations = duration if duration == 0 else duration.seconds
        return durations

#=====================================================================

    async def get01(flocation):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if not metadata or metadata == None:
            return 0, 0, 0
        width = metadata.get("width", 0)
        height = metadata.get("height", 0)
        duration = metadata.get("duration", 0)
        durations = duration if duration == 0 else duration.seconds
        return width, height, durations

#=====================================================================

    async def get02(flocation, secondzeros=0):
        metadato = createParser(flocation)
        metadata = extractMetadata(metadato)
        if metadata == None or metadata == Scripted.DATA01:
            return Scripted.DATA03, Scripted.DATA03, 0
        title = metadata.get("title", Scripted.DATA03)
        artist = metadata.get("artist", Scripted.DATA03)
        duration = metadata.get("duration", secondzeros)
        durations = duration if duration == 0 else duration.seconds
        return title, artist, durations

#=====================================================================





