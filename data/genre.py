#!/usr/bin/env python
from datetime import datetime

from sqlobject import *
from sqlobject.versioning import Versioning

class Genre(SQLObject):
    name = UnicodeCol(length=255)
    tmdb_id = IntCol(unique=True)
    movies = RelatedJoin('Media');
    
    def __str__(self):
        return self.name