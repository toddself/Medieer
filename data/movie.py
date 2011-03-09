#!/usr/bin/env python
from datetime import datetime
import os

from sqlobject import *
from sqlobject.versioning import Versioning

class Genre(SQLObject):
    name = UnicodeCol(length=255)
    tmdb_id = IntCol(unique=True)
    movies = RelatedJoin('Movie');
    
    def __str__(self):
        return self.name

class Movie(SQLObject):
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
    
    tmdb_id = IntCol(unique=True)
    imdb_id = UnicodeCol(length=64, default='')
    title = UnicodeCol(length=255, default='')
    year = IntCol(default=datetime.now().year)
    genres = RelatedJoin('Genre')
    mpaa = IntCol(default=UR)
    director = UnicodeCol(length=255, default='')
    actors = UnicodeCol(default='')
    description = UnicodeCol(default='')
    length = IntCol(default=0)
    poster_remote_URI = UnicodeCol(default='')
    poster_local_URI = UnicodeCol(default='')
    file_URI = UnicodeCol(default='')

    def _get_mpaa(self):
        return Movie.ratings[self._SO_get_mpaa()]

    def toxml(self):
        genres = []
        for g in self.genres:
            genres.append(g.name)
        
        genre = '/'.join(genres)
        
        output = '''
<video>
    <title>%s</title>
    <year>%s</year>
    <genre>%s</genre>
    <mpaa>%s</mpaa>
    <director>%s</director>
    <actors>%s</actors>
    <description>%s</description>
    <length>%s</length>
</video>
        ''' % (self.title, self.year, genre,
               self.mpaa, self.director, self.actors,
               self.description, self.length)
    
        return output
    

def connect():
    home = os.getenv("HOME")
    storagepath = '.movie_info'
    db_fn = 'movieinfo.sqlite'
    db_filepath = "%s/%s" % (home, storagepath)

    if not os.path.isdir(db_filepath):
        os.makedirs(db_filepath)

    db_filelocation = "%s/%s" % (db_filepath, db_fn)
    db_driver = 'sqlite'

    connection_string = "%s:%s" % (db_driver, db_filelocation)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection
    
    if not Movie.tableExists():
        Movie.createTable()
        
    if not Genre.tableExists():
        Genre.createTable()

if __name__ == '__main__':
    try:
        m = Movie(tmdb_id=0, imdb_id='tt2324', title="test", year=1996, mpaa=Movie.UR, director="test", actors="test", description="test", length=94)
        g = Genre(name="action", tmdb_id=123)
        m.addGenre(m)
    except AttributeError:
        connect()
        m = Movie(tmdb_id=0, imdb_id='tt2324', title="test", year=1996, mpaa=Movie.UR, director="test", actors="test", description="test", length=94)
        g = Genre(name="action", tmdb_id=123)
        m.addGenre(m)