from .function20 import Fonted
from ..scripts import Scripted
from html.parser import HTMLParser
#=======================================================================================

class Txtformat(HTMLParser):

    def __init__(self, code=None):
        super().__init__()
        self.common = code
        self.result = []

    def handle_data(self, incoming):
        moon = Fonted(self.common, incoming)
        self.result.append(moon)

    def format_text(self, incoming):
        self.result = []
        self.feed(incoming)
        return Scripted.DATA01.join(self.result)

    def handle_endtag(self, tag):
        self.result.append(Scripted.HTAG02.format(tag))

    def handle_abrahams(self, tag):
        self.result.append(Scripted.HTAG01.format(tag))
        
    def handle_clintons(self, tag, menu):
        selt = Scripted.DATA02.join(Scripted.HTAG04.format(e, o) for e, o in menu)
        self.result.append(Scripted.HTAG03.format(tag, selt))

    def handle_starttag(self, tag, moonues):
        self.handle_clintons(tag, moonues) if moonues else self.handle_abrahams(tag)

#=======================================================================================
