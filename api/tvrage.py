from urllib import quote_plus

from BeautifulSoup import BeautifulStoneSoup
from apibase import *
from data.models import NSCommon, Media

class TVRage(APIBase):
    apikey = 'SM0w3w3ATTXS3B9OobS9'
    path_format = '/myfeeds/%(api)s.php?key=%(apikey)s'
    protocol = 'http'
    host = 'services.tvrage.com'

    def pathParams(self):
        return {'api': self.method,
                'apikey': self.apikey}
    
    def lookup(self, title = '', series_id = 0, season = 0, episode = 0):
        if title:
            self.title = title
            self.method = 'search'
            self.search_term = "&show=%s" % quote_plus(self.title)
            
        elif series_id and not season and not episode:
            self.series_id = series_id
            self.method = 'showinfo'
            self.search_term = "&sid=%s" % self.series_id
            
        elif series_id and season and episode:
            self.series_id = series_id
            self.episode = episode
            self.season = season
            self.method = 'episodeinfo'
            self.search_term = "&sid=%s&ep=%sx%s" % (self.series_id, 
                                                     self.season, 
                                                     self.episode)
        
        else:
            raise AttributeError("You must provide enough data to make a query")
            
        
        if self.debug:
            print "Search term: ", self.search_term
            
        path = self.path_format % self.pathParams()
        self.makeURL(path, self.search_term, sep_char = '&')
        self.getResponse()
        
        serials = self.parseResponse(self.method)
        
        if self.method == 'search':
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
        self.soup = BeautifulStoneSoup(self._response_data)
        api_data = eval('self.%sParser' % method)(self.soup)
        return api_data
        
    def searchParser(self, soup):
        if self.debug:
            print "In searchParser"
        
        ids = []
        try:
            for show in soup.findAll('show'):
                ids.append(int(show.showid.text))
        except IndexError:
            raise APIError('No matches found for %s' % self.series)
        
        return ids
        
    def episodeinfoParser(self, soup):
        if self.debug:
            print 'In episodeinfoParser'
        
        e = APIMedia()
        e.title = soup.show.episode.title.text
        e.description = soup.show.episode.summary.text
        e.runtime = int(soup.show.runtime.text)
        e.director = []
        e.rating = Media.NONE
        e.poster_url = u''
        e.released = soup.show.episode.airdate.text
        e.media_type = Media.TV
        e.franchise = soup.show.find('name').text
        (season, episode) = soup.show.episode.number.text.split('x')
        e.season_number = int(season)
        e.episode_number = int(episode)
        e.ids = [{'ns': 'tvrage_episode', 'value': soup.show.episode.number.text},]
        genres = []
        for genre in soup.findAll('genre'):
            g = APIGenre()
            g.name = genre.text
            genres.append(g)
        e.genres = genres
        e.actors = []
        
        return [e,]

    def showinfoParser(self, soup):
        if self.debug:
            print 'In showinfoParser'
        
        s = APISeries()
        try:
            s.title = soup.showinfo.showname.text
        except AttributeError:
            return None
        
        try:
            s.description = soup.showinfo.summary.text
        except AttributeError:
            s.description = ''
            
        try:
            s.image_url = soup.showinfo.image.text
        except AttributeError:
            s.image_url = ''
        
        s.ids = [{'ns': 'tvrage_series', 'value': int(soup.showinfo.showid.text)},]

        return [s, ]

        
    def episode_listParser(self, soup):
        if self.debug:
            print "In episode_listParser"
            
        pass
        
if __name__ == '__main__':
    tvr = TVRage()
    series = tvr.lookup("Justified")
    print series