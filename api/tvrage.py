import re
from StringIO import StringIO

from lxml import objectify
from apibase import *
from data.models import NSCommon, Media

class TVDB(APIBase):
    apikey = 'SM0w3w3ATTXS3B9OobS9'
    path_format = '/myfeeds/%(api)s.php?key=%(apikey)s'
    protocol = 'http'
    host = 'services.tvrage.com'

    def pathParms(self):
        return {'api': self.method,
                'apikey': self.apikey}
    
    def lookup(self, title = '', series_id = 0, season = 0, episode = 0):
        if title:
            self.title = title
            self.method = 'search'
            self.search_term = "&show=%s" % self.series
            
        elif series_id and not season and not episode:
            self.series_id = series_id
            self.method = 'showinfo'
            self.search_term = "&sid=%s" % self.series_id
            
        elif series_id and season and episode:
            self.series_id = series_id
            self.episode = episode
            self.series = series
            self.method = 'episodeinfo'
            self.search_term = "&sid=%s&ep=%sx%s" % (self.series_id, 
                                                     self.series, 
                                                     self.episode)
        
        else:
            raise AttributeError("You must provide enough data to make a query")
            
        
        if self.debug:
            print "Search term: ", self.search_term
            
        path = self.path_format % self.pathParams
        self.makeURL(path, self.search_term)
        self.getResponse()
        
        serials = self.parseResponse(self.method)
        
        if self.method = 'search':
            if self.debug:
                print "We looked up the IDs for these shows:"
                print serials
                info = []
            for series_id in serials:
                if self.debug:
                    print 'Looking up: ', series_id
                info.append(self.lookup(series_id=series_id)[0])
            return info
            
        return serials
    
    def parseResponse(self, method):
        self.data_dict = objectify.fromstring(self._response_data).__dict__
        if len(self.data_dict) < 1:
            raise APIError("No information found for %s" % series)
        api_data = eval('self.%sParser' % method)(self.data_dict)
        return api_data
        
    def searchParser(self, dd):
        if self.debug:
            print "In searchParser"
        
        ids = []
        for 
        pass
        
    def episodeinfoParser(self):
        pass
        
    def showinfoParser(self, dd):
        if self.debug:
            print 'In showinfoParser'
            
        series = APISeries()
        series.name = dd.get('showname', '')
        series.ids = [{'ns': 'tvrage', 'value': int(dd.get('showid', 0)),]
        series.description = dd.get('summary', '')
        series.image_url = dd.get('image', '')
        
        return series

        
    def episode_listParser(self):
        pass