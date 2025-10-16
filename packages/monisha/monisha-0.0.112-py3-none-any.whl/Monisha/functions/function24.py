from ..scripts import Scripted
#==========================================================

class SafeDict(dict):

    def _missing_(self, key):
        return Scripted.DATA01

    def clean(self, text):
        return text.replace("{}", Scripted.DATA01)

#==========================================================

class CustDict(dict):

    def update(self, key, value):
        if key in self:
            self[key] = value
        else:
            pass

    def insert(self, key, value):
        if key not in self:
            self[key] = value
        else:
            pass

#==========================================================
