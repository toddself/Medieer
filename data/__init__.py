from sqlobject import connectionForURI, sqlhub

from models import NSID, Media, Genre, Settings, Person
from MediaInfo import __APP_NAME__

def connect(dirs):
    db_driver = 'sqlite'
    connection_string = "%s://%s" % (db_driver, db_filelocation)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection