#!/usr/bin/env python
from datetime import datetime

from sqlobject import *
from sqlobject.versioning import Versioning

class NSCommon():
    def _set_id(ns, value):
        n = NSID(ns=NSID.sites.index(ns), value=str(value))
        setattr(n, self.__class__.__name__, self)
    
    def _get_id(ns, value):
        return list(NSID.select(AND(NSID.q.ns==ns, getattr(NSID.q, self.__class__.__name__)==self)))[0].value

class Actor(SQLObject, NSCommon):
    name = UnicodeCol(length=255)
    nsids = MultipleJoin('NSID')

class Settings(SQLObject):
    key = UnicodeCol(length=255, unique=True)
    value = UnicodeCol(length=255)

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
    
    def _set_value(self, value):
        if self.ns == self.IMDB:
            import re
            imdb_pattern = list(Settings.select(Settings.q.key=="imdb_id_pattern"))[0].value
            if re.search(imdb_pattern, value):
                self._SO_set_value(value)
            else:
                raise ValueError('ID does not match IMDB pattern')
        else:
            self._SO_set_value(unicode(value))

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
    year = IntCol(default=datetime.now().year)
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
            raise DataError("%s is not a known rating")

class DataError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

