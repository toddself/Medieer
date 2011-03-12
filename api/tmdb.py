#!/usr/bin/env python
import json
import re

from apibase import *
from data.models import NSCommon, Media

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
        self.search_term = search_term
        if self.domain == 'movie':
            if isinstance(self.search_term , str):
                if re.search(NSCommon().imdb_id_pattern, self.search_term):
                    self.method = 'imdbLookup'
                else:
                    self.method = 'search'
            else:
                self.method = 'getInfo'
        elif self.domain == 'genres':
            self.method = 'getList'
        else:
            raise ValueError('API not implemented for %s' % self.domain)
            
        self.api_method = self.getAPIMethod(self.domain, self.method)
        path = self.path_format % self.pathParams()
        self.makeURL(path, self.search_term)
        self.getResponse()
        
        movies = self.parseResponse(self.method)

        if self.method == 'search' and self.domain == 'movie':
            info = []
            for movie_id in movies:
                info.append(self.lookup(movie_id)[0])
            return info
        
        return movies
        
    def parseResponse(self, method):
        self.json_data = json.loads(self._response_data)
        if "Nothing found" in self.json_data:
            raise APIError("No information found for ")
        api_data = eval('self.%sParser' % method)(self.json_data)
        return api_data
    
    def imdbLookupParser(self, api_data):
        return self.getInfoParser(api_data)

    def getInfoParser(self, api_data):
        d = api_data[0]
        movie = APIMedia()
        movie.title = d.get('name', '')
        movie.description = d.get('overview', '')
        movie.released = d.get('released', '')
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
        ids = []
        for d in api_data:
            ids.append(d.get('id', 0))
        
        return ids
    
    def getListParser(self, api_data):
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