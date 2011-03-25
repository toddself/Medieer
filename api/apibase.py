#!/usr/bin/env python
from urllib2 import urlopen, HTTPError
from urllib import quote_plus

class APISeries():
    name = ''
    ids = []
    description = ''
    image_url = ''

class APIMedia():
    title = ''
    genres = []
    actors = []
    description = ''
    runtime = ''
    director = ''
    ids = []
    rating = ''
    poster_url = ''
    released = ''
    media_type = ''
    franchise = ''
    episode_number = ''
    season_number = ''
    
    def __init__(self, **kw):
        for k in kw.keys():
            setattr(self, k, kw[k])
            
    def __str__(self):
         return self.title
         
     def __repr__(self):
         return self.title
    
class APIGenre():
    name = u''
    ids = []
    
    def __init__(self, **kw):
        for k in kw.keys():
            setattr(self, k, kw[k])
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return self.name

class APIPerson():
    name = u''
    ids = []
    job = ''

    def __init__(self, **kw):
        for k in kw.keys():
            setattr(self, k, kw[k])

    def __str__(self):
        return self.name
        
class APIBase():
    lang = 'en'
        
    def __init__(self, debug=False):
        self.debug = debug
    
    def _hasLeadingChar(self, chr, term):
        try:
            if len(term) > 0:
                try:
                    term.index(chr)
                except ValueError:
                    return False
                else:
                    return True
            else:
                return True
        except:
            return False
        
    def makeURL(self, path, term='', sep_char = '/'):
        if not self._hasLeadingChar(sep_char, term):
            term = '%s%s' % (sep_char, term)
        
        self.url = "%(proto)s://%(host)s%(path)s%(term)s" % \
                    {'proto': self.protocol,
                     'host': self.host,
                     'path': path,
                     'term': quote_plus(term)}
                     
        if self.debug:
            print "Generated URL: ", self.url
            
    def getResponse(self):
        if not self.url:
            raise APIError('No defined URL to access')
        
        try:
            self.server_response = urlopen(self.url)
        except HTTPError:
            raise APIError("Couldn't open %s for reading" % self.url)

        self._server_msg = self.server_response.msg
        
        if "OK" not in self._server_msg:
            raise APIError("Server responded with something I can't handle.")
        else:
            self._response_data = self.server_response.read()

class APIError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)    
            