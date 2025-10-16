import os
import json
from ..scripts import Smbo, Scripted
#====================================================================

class readers:

    def get01(location=Scripted.DATA14):
        main = os.getcwd() + Smbo.DATA03 + location
        with open(main, 'r') as files:
            moonus = json.load(files)

        return moonus

#====================================================================
