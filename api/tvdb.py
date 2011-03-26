import re

from apibase import *
from data.models import NSCommon, Media

class TVDB(APIBase):
    apikey = '1B9D1199533C99BB'
    path_format = '/api/%(api)s?%(method)s=%(term)s'
    protocol = 'http'
    host = 'www.thetvdb.com'

    def lookup(self, title_string):
        self.parseTitleFromFilename(title_string)
        
        self.getSeries()
        
    def getSeries(self):
        pass