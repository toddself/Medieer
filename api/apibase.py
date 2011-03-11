#!/usr/bin/env python
from urllib2 import urlopen, HTTPError
from urllib import quote_plus

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
    
    def __init__(self):
        pass
    
    def _hasLeadingSlash(self, term):
        try:
            if len(term) > 0:
                try:
                    term.index('/')
                except ValueError:
                    return False
                else:
                    return True
            else:
                return True
        except:
            return False
        
    def makeURL(self, path, term=''):
        if not self._hasLeadingSlash(term):
            term = '/%s' % term
        
        self.url = "%(proto)s://%(host)s%(path)s%(term)s" % \
                    {'proto': self.protocol,
                     'host': self.host,
                     'path': path,
                     'term': quote_plus(term)}
            
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
            