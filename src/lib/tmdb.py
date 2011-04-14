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

import json
import re

from pubsub import pub

from apibase import *
from data.models import NSCommon, Media, Genre

def import_genre_data():
    # import genre data
    pub.sendMessage("LOGGER",
                    module=__name__,
                    level='DEBUG'.
                    msg="Getting default genre data")
    t = TMDB()
    genres = t.lookup(domain='genres')
    for genre in genres:
      g = Genre()
      g.fromAPIGenre(genre)


class TMDB(APIBase):
    path_format = '/%(version)s/%(api)s/%(lang)s/%(output)s/%(apikey)s'
    apikey = '32143db63692aa6a5cb01336cc06211b'
    protocol = 'http'
    host = 'api.themoviedb.org'
    version = '2.1'
    output = 'json'
    api = 'tmdb'
    
    def getAPIMethod(self, domain, method):
        calledAPI = "%s.%s" % (domain.capitalize(), method)
        return calledAPI
    
    def pathParams(self):
        return {'version': self.version, 
                'api': self.api_method,
                'lang': self.lang,
                'output': self.output,
                'apikey': self.apikey,}

    def lookup(self, search_term = '', domain = 'movie'):
        self.domain = domain
        
        if isinstance(search_term, str):
            self.search_term = search_term.replace('_', ' ')
        else:
            self.search_term = search_term
        
        self.log.debug("Parsed search term: %s" % self.search_term)
        
        if self.domain == 'movie':
            if isinstance(self.search_term , str):
                if re.search(NSCommon().imdb_id_pattern, self.search_term):
                    self.method = 'imdbLookup'
                    self.log.debug("IMDB ID recieved: %s" % self.search_term)
                else:
                    self.log.debug("Movie Name received: %s" % self.search_term)
                    self.method = 'search'
            else:
                self.method = 'getInfo'
        elif self.domain == 'genres':
            self.method = 'getList'
        else:
            self.log.critical('API not implemented for %s' % self.domain)
            raise ValueError('API not implemented for %s' % self.domain)

        self.log.debug("Method: %s" % self.method)
            
        self.api_method = self.getAPIMethod(self.domain, self.method)
        path = self.path_format % self.pathParams()
        self.makeURL(path, self.search_term)
        self.getResponse()
        
        movies = self.parseResponse(self.method)

        if self.method == 'search' and self.domain == 'movie':
            self.log.debug('We looked up the IDs for these movies:')
            self.log.debug(movies)
            info = []
            for movie_id in movies:
                self.log.debug("Looking up: %s" % movie_id)
                info.append(self.lookup(movie_id)[0])
            return info
        
        return movies
        
    def parseResponse(self, method):
        self.json_data = json.loads(self._response_data)
        if "Nothing found" in self.json_data:
            self.log.critical("No information found for %s" % self.search_term)
            raise APIError("No information found for %s" % self.search_term)
        api_data = eval('self.%sParser' % method)(self.json_data)
        return api_data
    
    def imdbLookupParser(self, api_data):
        self.log.debug("In imdbLookupParser")
        return self.getInfoParser(api_data)

    def getInfoParser(self, api_data):
        self.log.debug("In getInfoParser")
    
        d = api_data[0]
        movie = APIMedia()
        movie.title = d.get('name', '')
        movie.description = d.get('overview', '')
        movie.released = d.get('released', '2010-06-23')
        movie.runtime = d.get('runtime', '')
        movie.rating = d.get('certification', 'NR')
        movie.genres = self.getGenres(d.get('genres',[]))
        movie.actors = self.getPerson(d.get('cast', []), 'actor')
        movie.director = self.getPerson(d.get('cast', []), 'director')
        movie.ids = [{'ns': 'tmdb', 'value': d.get('id', 0)}, {'ns': 'imdb', 'value': d.get('imdb_id', 'tt0000000')}]
        movie.poster_url = self.getPoster(d.get('posters', []))
        movie.media_type = Media.MOVIES
        movie.franchise = ''
        
        return [movie,]
        
    def searchParser(self, api_data):
        self.log.debug("In searchParser")
        ids = []
        for d in api_data:
            ids.append(d.get('id', 0))
        
        return ids
    
    def getListParser(self, api_data):
        self.log.debug("In getListParser")
        genres = self.getGenres(api_data[1:])
        return genres
        
    def getGenres(self, genre_list):
        genres = []
        for genre in genre_list:
            g = APIGenre()
            g.name = genre.get('name', '')
            g.ids = [{'ns': 'tmdb', 'value': genre.get('id', 0)}]
            genres.append(g)
            
        return genres
        
    def getPerson(self, cast_list, search_job):
        people = []
        for cast in cast_list:
            job = cast.get('job', '')
            if job.lower() == search_job:
                person = APIPerson()
                person.name = cast.get('name', '')
                person.role = job
                person.id = [{'ns': 'tmdb', 'value': cast.get('id', 0)}]
                people.append(person)
            
        return people
        
    def getPoster(self, poster_list):
        poster_url = ''
        for image in poster_list:
            poster = image.get('image', {})
            if poster.get('size', '') == 'cover' and poster.get('url', False):
                poster_url = poster.get('url')
            
            if not poster_url and poster.get('size', None) == 'mid' and poster.get('url', False):
                poster_url = poster.get('url')
        
        return poster_url