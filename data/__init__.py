import os
from os.path import join as fjoin

from sqlobject import connectionForURI, sqlhub

from models import NSID, Media, Genre, Settings, DataError, Actor

def connect():
    storagepath = os.getcwd()
    db_fn = 'mediainfo.sqlite'
    db_filepath = fjoin('data', storagepath)

    if not os.path.isdir(db_filepath):
        os.makedirs(db_filepath)

    db_filelocation = fjoin(db_filepath, db_fn)
    db_driver = 'sqlite'

    connection_string = "%s:%s" % (db_driver, db_filelocation)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection
    
    if not Media.tableExists():
        Media.createTable()
        
    if not Genre.tableExists():
        Genre.createTable()
        
    if not Settings.tableExists():
        Settings.createTable()
        s = Settings(key='imdb_id_pattern', value="t{2}\d{7}$")
        
    if not NSID.tableExists():
        NSID.createTable()
        
    if not Actor.tableExists():
        Actor.createTable()

connection = connect()