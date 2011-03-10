import os
from os.path import join as fjoin

from appdirs import AppDirs
from sqlobject import connectionForURI, sqlhub

from models import NSID, Media, Genre, Settings, DataError, Person
from main import __APP_NAME__, __APP_AUTHOR__, __VERSION__

def connect():
    dirs = AppDirs(__APP_NAME__, __APP_AUTHOR__, version=__VERSION__)
    db_fn = '%s.sqlite' % __APP_NAME__

    if not os.path.isdir(dirs.user_data_dir):
        os.makedirs(dirs.user_data_dir)

    db_filelocation = fjoin(dirs.user_data_dir, db_fn)
    db_driver = 'sqlite'

    connection_string = "%s://%s" % (db_driver, db_filelocation)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection
    
    if not Media.tableExists():
        Media.createTable()
        
    if not Genre.tableExists():
        Genre.createTable()
        
    if not Settings.tableExists():
        Settings.createTable()
                
    if not NSID.tableExists():
        NSID.createTable()
        
    if not Person.tableExists():
        Person.createTable()

connection = connect()