from .collections import SMessage
#========================================================================

class FMagic:

    def get01(file):
        try:
            from magic import Magic
            mimees = Magic(mime=True)
            mimeos = mimees.from_file(file)
            mimemo = mimeos or "text/plain"
            return SMessage(filetype=mimemo)
        except Exception as errors:
            return SMessage(filetype="application/zip", errors=errors)

#========================================================================

    async def get02(file):
        try:
            from magic import Magic
            mimees = Magic(mime=True)
            mimeos = mimees.from_file(file)
            mimemo = mimeos or "text/plain"
            return SMessage(filetype=mimemo)
        except Exception as errors:
            return SMessage(filetype="application/zip", errors=errors)

#========================================================================
