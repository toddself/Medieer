#!/usr/bin/env python
from datetime import datetime

from sqlobject import *
from sqlobject.versioning import Versioning

class Settings(SQLObject):
    key = UnicodeCol(length=255, unique=True)
    value = UnicodeCol(length=255)

class Genre(SQLObject):
    name = UnicodeCol(length=255)
    movies = RelatedJoin('Media')
    nsid = MultipleJoin('SysRef')
    
    def __str__(self):
        return self.name

class SysRef(SQLObject):
    TMDB = 0
    IMDB = 1
    TVDB = 2
    
    sites = ["tmdb", "imdb", "tvdb"]
    
    ns = IntCol(default=SysRef.TMDB)
    value = UnicodeCol(default='')
    
    def _get_ns(self):
        return self.sites[self._SO_get_ns()]
    
    def _set_ns(self, value):
        if int(value) and value < len(self.sites):
            self._SO_set_ns(value)
        elif value in self.sites:
            self._SO_set_ns(self.sites.index(value))
        else:
            raise DataError('External site namespace unrecognized: %s' % value)

class Media(SQLObject):
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
    
    nsid = MultipleJoin('SysRef')    
    title = UnicodeCol(length=255, default='')
    year = IntCol(default=datetime.now().year)
    genres = RelatedJoin('Genre')
    rating = IntCol(default=UR)
    director = UnicodeCol(length=255, default='')
    actors = UnicodeCol(default='')
    description = UnicodeCol(default='')
    length = IntCol(default=0)
    poster_remote_URI = UnicodeCol(default='')
    poster_local_URI = UnicodeCol(default='')
    file_URI = UnicodeCol(default='')

    def _get_rating(self):
        return self.ratings[self._SO_get_rating()]
    
    def _set_rating(self, value):
        if int(value) and value < len(self.ratings):
            self._SO_set_rating(value)
        elif value in self.ratings:
            self._SO_set_rating(self.ratings.index(value))
        else:
            raise DataError("%s is not a known rating")

class DataError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

