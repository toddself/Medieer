from sqlobject import connectionForURI, sqlhub

from models import NSID, Media, Genre, Settings, Person, get_setting

def connect(db_filelocation):
    db_driver = 'sqlite'
    connection_string = "%s://%s" % (db_driver, db_filelocation)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection