#!/usr/bin/env python
from datetime import datetime

from sqlobject import *
from sqlobject.versioning import Versioning

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
    tmdb_id_pattern = '^\d+$'
    
    def _set_id(self, ns, value):
        n = NSID(ns=NSID.sites.index(ns), value=str(value))
        setattr(n, self.__class__.__name__, self)
    
    def _get_id(self, ns):
        return list(NSID.select(AND(NSID.q.ns==ns, getattr(NSID.q, self.__class__.__name__)==self)))[0].value
        
    def _set_tmdb_id(self, value):
        if isinstance(value, int):
            tmdb_id = str(value)
        else:
            import re
            if re.search(self.tmdb_id_pattern, value):
                tmdb_id = value
            else:
                raise ValueError('TMDB IDs must be integers. %s' % value)
        
        self._set_id(NSID.TMDB, tmdb_id)
        
    def _set_imdb_id(self, value):
        if isinstance(value, str):
            import re
            if re.search(self.imdb_id_pattern, value):
                imdb_id = value
            else:
                raise ValueError('IMDB IDs must be in the form of two letters followed by seven digits')
        else:
            raise ValueError('IMDB IDs must be in the form of two letters followed by seven digits')
        
        self._set_id(NSID.IMDB, imdb_id)
        
    def _set_tvdb_id(self, value):
        self._set_id(NSID.TVDB, str(value))
        
    def _get_tmdb_id(self):
        return self._get_id(NSID.TMDB)

    def _get_imdb_id(self):
        return self._get_id(NSID.IMDB)
    
    def _get_tvdb_id(self):
        return self._get_id(NSID.TVDB)

class Actor(SQLObject, NSCommon):
    name = UnicodeCol(length=255)
    nsids = MultipleJoin('NSID')

class Settings(SQLObject):
    key = StringCol(length=255, unique=True)
    value = StringCol(length=255)

class Genre(SQLObject, NSCommon):
    name = UnicodeCol(length=255)
    movies = RelatedJoin('Media')
    nsids = MultipleJoin('NSID')
    
    def __str__(self):
        return self.name

class NSID(SQLObject):
    TMDB = 0
    IMDB = 1
    TVDB = 2
    sites = ["tmdb", "imdb", "tvdb"]
    
    ns = IntCol(default=TMDB)
    value = UnicodeCol(default='')
    actor = ForeignKey('Actor', default=0)
    media = ForeignKey('Media', default=0)
    genre = ForeignKey('Genre', default=0)
    nsindex = DatabaseIndex('ns', 'value', unique=True)
    
    def _get_ns(self):
        return self.sites[self._SO_get_ns()]
    
    def _set_ns(self, value):
        if isinstance(value, int) and value < len(self.sites):
            self._SO_set_ns(value)
        elif value in self.sites:
            self._SO_set_ns(self.sites.index(value))
        else:
            raise ValueError('External site namespace unrecognized: %s' % value)

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
    ratings = ['G', 'NC-17', 'PG', 'PG-13', 'R', 'UR', 'UNRATED', 'NR', 'TV-Y', 'TV-Y7', 'TV-Y7-FV', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA']
    
    nsids = MultipleJoin('NSID')    
    title = UnicodeCol(length=255, default='')
    released = DateTimeCol(default=datetime.now())
    genres = RelatedJoin('Genre')
    rating = IntCol(default=UR)
    director = UnicodeCol(length=255, default='')
    actors = MultipleJoin('Actor')
    description = UnicodeCol(default='')
    length = IntCol(default=0)
    poster_remote_URI = UnicodeCol(default='')
    poster_local_URI = UnicodeCol(default='')
    file_URI = UnicodeCol(default='')
    
    def _get_tmdb_id(self):
        return list(NSID.select(AND(NSID.q.media==self, NSID.q.ns==NSID.TMDB)))[0].value
    
    def _set_tmdb_id(self, value):
        pass

    def _get_rating(self):
        return self.ratings[self._SO_get_rating()]
    
    def _set_rating(self, value):
        if isinstance(value, int) and value < len(self.ratings):
            self._SO_set_rating(value)
        elif value in self.ratings:
            self._SO_set_rating(self.ratings.index(value))
        else:
            raise ValueError("%s is not a known rating")
    
    def _set_year