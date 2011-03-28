#!/usr/bin/env python
# This file is part of Medieer.
# 
#     Medieer is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Medieer is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

from urllib2 import urlopen, HTTPError
from urllib import quote_plus

class APISeries():
    title = ''
    ids = []
    description = ''
    image_url = ''
    
    def __init__(self, **kw):
        for k in kw.keys():
            setattr(self, k, kw[k])
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return self.name

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
    episode_number = 0
    season_number = 0
    
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
        
    def __init__(self, log):
        self.log = log
    
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
        
        if "&" not in sep_char:
            term = quote_plus(term)
        
        self.url = "%(proto)s://%(host)s%(path)s%(term)s" % \
                    {'proto': self.protocol,
                     'host': self.host,
                     'path': path,
                     'term': term}
                     
        self.log.debug("Generated URL: %s" % self.url)
            
    def getResponse(self):
        if not self.url:
            self.log.critical('No defined URL to access')
            raise APIError('No defined URL to access')
        
        try:
            self.server_response = urlopen(self.url)
        except HTTPError:
            self.log.critical("Couldn't open %s for reading" % self.url)
            raise APIError("Couldn't open %s for reading" % self.url)

        self._server_msg = self.server_response.msg
        
        if "OK" not in self._server_msg:
            self.log.critical("Server responded with something I can't handle.")
            raise APIError("Server responded with something I can't handle.")
        else:
            self._response_data = self.server_response.read()

class APIError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)    
            