from sqlobject import connectionForURI, sqlhub

from models import Series, NSID, Media, Genre, Settings, Person, get_setting

TV = Media.TV
MOVIES = Media.MOVIES
media_types = Media.media_types

def connect(db_filelocation):
    db_driver = 'sqlite'
    connection_string = "%s://%s" % (db_driver, db_filelocation)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection