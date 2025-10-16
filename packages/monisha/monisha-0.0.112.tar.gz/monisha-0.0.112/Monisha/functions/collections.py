class SMessage:

    def __init__(self, **kwargs):
        self.errors = kwargs.get("errors", None)
        self.result = kwargs.get("result", None)
        self.numfiles = kwargs.get('numfiles', 0)
        self.filesize = kwargs.get('filesize', 0)
        self.numusers = kwargs.get("numusers", 0)
        self.allfiles = kwargs.get('allfiles', [])
        self.taskcode = kwargs.get("taskcode", 404)
        self.filename = kwargs.get("filename", None)
        self.location = kwargs.get('location', None)
        self.filetype = kwargs.get("filetype", None)
        self.extension = kwargs.get("extension", None)
        self.thumbnail = kwargs.get("thumbnail", None)

