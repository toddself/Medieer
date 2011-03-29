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

from datetime import datetime

from sqlobject import *
from sqlobject.versioning import Versioning

def get_setting(setting_key):
    try:
        setting =  list(Settings.select(Settings.q.key==setting_key))[0].value
        if setting == 'true' or setting == 'false':
            return eval(setting.capitalize())
        else:
            return setting
    except:
        return ''

class NSCommon():
    '''
    NSCommon defines a base set of getter and setter methods allowing
    ease of access to NSID class.  This way specific namespace ids can be
    accessed through instance attributes.
    
    ex:
    
    Actor.tmdb_id
    Media.imdb_id
    '''
    
    imdb_id_pattern = 't{2}\d{7}$'
    tvdb_id_pattern = tvrage_series_id_pattern = tmdb_id_pattern = '^\d+$'
    tvrage_episode_id_pattern = '^\d{1,3}x\d{1,3}$'
    
    def _set_id(self, ns, value):
        n = NSID(ns=NSID.sites.index(ns), value=str(value))
        setattr(n, self.__class__.__name__, self)
    
    def _get_id(self, ns):
        return list(NSID.select(AND(NSID.q.ns==ns, getattr(NSID.q, self.__class__.__name__.lower())==self)))[0].value
        
    def set_tmdb_id(self, value):
        if isinstance(value, int):
            tmdb_id = str(value)
        else:
            import re
            if re.search(self.tmdb_id_pattern, value):
                tmdb_id = value
            else:
                raise ValueError('TMDB IDs must be integers. %s' % value)
        
        self._set_id(NSID.TMDB, tmdb_id)
        
    def set_imdb_id(self, value):
        if isinstance(value, str):
            import re
            if re.search(self.imdb_id_pattern, value):
                imdb_id = value
            else:
                raise ValueError('IMDB IDs must be in the form of two letters followed by seven digits')
        else:
            raise ValueError('IMDB IDs must be in the form of two letters followed by seven digits')
        
        self._set_id(NSID.IMDB, imdb_id)
        
    def set_tvdb_id(self, value):
        self._set_id(NSID.TVDB, str(value))
    
    def set_tvrage_episode_id(self, value):
        self._set_id(NSID.TVRAGE_EPISODE, str(value))

    def set_tvrage_series_id(self, value):
        self._set_id(NSID.TVRAGE_SERIES, str(value))        
        
    def get_tmdb_id(self):
        return self._get_id(NSID.TMDB)

    def get_tvrage_series_id(self):
        return self._get_id(NSID.TVRAGE_SERIES)
        
    def get_tvrage_episode_id(self):
        return self._get_id(NSID.TVRAGE_EPISODE)

    def get_imdb_id(self):
        return self._get_id(NSID.IMDB)
    
    def get_tvdb_id(self):
        return self._get_id(NSID.TVDB)

class Person(SQLObject, NSCommon):
    name = UnicodeCol(length=255, default='')
    nsids = MultipleJoin('NSID')
    job = UnicodeCol(length=255, default='')
    media = RelatedJoin('Media')
    
    def fromAPIPerson(self, APIPerson):
        self.name = APIPerson.name
        self.job = APIPerson.job
        for ns in APIPerson.ids:
            n = NSID(ns=ns['ns'], value=ns['value'], person=self)
        
    def __str__(self):
        return self.name

class Settings(SQLObject):
    key = StringCol(length=255, unique=True)
    value = StringCol(length=255)
    
    def __str__(self):
        return self.value

class Genre(SQLObject, NSCommon):
    name = UnicodeCol(length=255, default='')
    media = RelatedJoin('Media')
    nsids = MultipleJoin('NSID')
    
    def fromAPIGenre(self, APIGenre):
        self.name = APIGenre.name
        for ns in APIGenre.ids:
            n = NSID(ns=ns['ns'], value=ns['value'], genre=self)
    
    def __str__(self):
        return self.name

class NSID(SQLObject):
    TMDB = 0
    IMDB = 1
    TVDB = 2
    TVRAGE_SERIES = 3
    TVRAGE_EPISODE = 4
    sites = ["tmdb", "imdb", "tvdb", "tvrage_series", "tvrage_episode"]
    
    ns = IntCol(default=TMDB)
    value = UnicodeCol(default='')
    person = ForeignKey('Person', default=0)
    media = ForeignKey('Media', default=0)
    genre = ForeignKey('Genre', default=0)
    series = ForeignKey('Series', default=0)
    
    def _get_ns(self):
        return self.sites[self._SO_get_ns()]
    
    def _set_ns(self, value):
        if isinstance(value, int) and value < len(self.sites):
            self._SO_set_ns(value)
        elif value in self.sites:
            self._SO_set_ns(self.sites.index(value))
        else:
            raise ValueError('External site namespace unrecognized: %s' % value)
    
    def _set_value(self, value):
        if not isinstance(value, str):
            self._SO_set_value(str(value))
        else:
            self._SO_set_value(value)
    
    def __str__(self):
        return "%s: %s" % (self.sites.index(self.ns), self.value)
        
class Series(SQLObject, NSCommon):
    name = UnicodeCol(length=255, default='')
    nsids = MultipleJoin('NSID')
    description = UnicodeCol(default='')
    poster_remote_URI = UnicodeCol(default='')
    poster_local_URI = UnicodeCol(default='')
    
    def fromAPISeries(self, APISeries):
        self.name = APISeries.title
        self.description = APISeries.description
        self.poster_remote_URI = APISeries.image_url
        
        for nsid in APISeries.ids:
            n = NSID(ns=nsid['ns'], value=nsid['value'], series=self)

class Media(SQLObject, NSCommon):
    G = 0
    NC17 = 1
    PG = 2
    PG13 =3
    R = 4
    UR = 5
    UNRATED = 6
    NR = 7
    TVY = 8
    TVY7 = 9
    TVY7FV = 10
    TVG = 11
    TVPG = 12
    TV14 = 13
    TVMA = 14
    NONE = 15
    ratings = ['G', 'NC-17', 'PG', 'PG-13', 'R', 'UR', 'UNRATED', 'NR', 'TV-Y', 'TV-Y7', 'TV-Y7-FV', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA', 'None']
    
    MOVIES = 0
    TV = 1
    media_types = ['Movies', 'TV']
    
    nsids = MultipleJoin('NSID')    
    title = UnicodeCol(length=255, default='')
    released = DateTimeCol(default=datetime.now())
    genres = RelatedJoin('Genre')
    rating = IntCol(default=UR)
    director = ForeignKey('Person', default=0)
    actors = RelatedJoin('Person', addRemoveName='Actor')
    description = UnicodeCol(default='')
    runtime = IntCol(default=0)
    poster_remote_URI = UnicodeCol(default='')
    poster_local_URI = UnicodeCol(default='')
    file_URI = UnicodeCol(default='')
    media_type = IntCol(default=MOVIES)
    franchise = ForeignKey('Series', default=0)
    episode_number = IntCol(default=0)
    season_number = IntCol(default=0)
    
    def fromAPIMedia(self, APIMedia):
        self.title = APIMedia.title
        self.released = APIMedia.released
        self.rating = APIMedia.rating
        self.description = APIMedia.description
        self.poster_remote_URI = APIMedia.poster_url
        self.runtime = APIMedia.runtime
        self.media_type = APIMedia.media_type
        if APIMedia.franchise:
            try:
                franchise = list(Series.select(Series.q.name==APIMedia.franchise))[0]
            except IndexError:
                raise AttributeError("The series must exist before an episode can")
            self.franchise = franchise
        self.episode_number = int(APIMedia.episode_number)
        self.season_number = int(APIMedia.season_number)
        
        if len(APIMedia.director):
            d = Person()
            d.fromAPIPerson(APIMedia.director[0])
            self.director = d

        for nsid in APIMedia.ids:
            n = NSID(ns=nsid['ns'], value=nsid['value'], media=self)
        
        if len(APIMedia.actors):
            for actor in APIMedia.actors:
                a = Person()
                a.fromAPIPerson(actor)
                self.addActor(a)

        if len(APIMedia.genres):
            for genre in APIMedia.genres:
                g = Genre()
                g.fromAPIGenre(genre)
                self.addGenre(g)
    
    def _set_media_type(self, value):
        if isinstance(value, int) and value < len(self.media_types):
            self._SO_set_media_type(value)
        elif value in self.media_types:
            self._SO_set_media_type(self.media_types.index(value))
        else:
            raise ValueError('%s is not a valid media type' % value)
        
    def _get_rating(self):
        return self.ratings[self._SO_get_rating()]
    
    def _set_rating(self, value):
        if isinstance(value, int) and value < len(self.ratings):
            self._SO_set_rating(value)
        elif value in self.ratings:
            self._SO_set_rating(self.ratings.index(value))
        else:
            raise ValueError("%s is not a known rating")
    
    def _set_released(self, value):
        if isinstance(value, datetime):
            self._SO_set_released(value)
        else:
            try:
                d = datetime.strptime(value, '%Y-%m-%d')
                self._SO_set_released(d)
            except ValueError:
                raise ValueError('%s is not in the form of %%Y-%%m-%%d' % value)
                
    def _get_media_type(self):
        return self.media_types[self._SO_get_media_type()]
                
    def listActors(self):
        actors = []
        for actor in self.actors:
            actors.append(actor.name)
        
        return actors
        
    def listGenres(self, prepend_media_type=True):
        genres = []
        for genre in self.genres:
            if prepend_media_type:
                g = "[%s/%s]" % (self.media_type, genre.name)
            else:
                g = genre.name
            genres.append(g)
        
        return genres
    
    def _get_codec(self):
        if self.file_URI:
            return self.file_URI.rsplit('.', 1)[1]
        else:
            return ''
            
    def __str__(self):
        return self.title