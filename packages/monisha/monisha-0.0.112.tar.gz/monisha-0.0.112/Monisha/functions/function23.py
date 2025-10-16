import socket
import requests
from ..scripts import Apis
#====================================================================

class Internet:

    def get01():
        moones = requests.get(Apis.DATA02)
        moonus = moones.json()
        return moonus.get('ip', None)

#====================================================================

    def get02(): # LOCAL IP
        moones = socket.gethostname()
        moonus = socket.gethostbyname(moones)
        return moonus

#====================================================================
