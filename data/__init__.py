import os

from sqlobject import connectionForURI, sqlhub

from models import SysRef, Media, Genre, Settings

def connect():
    storagepath = os.getcwd()
    db_fn = 'movieinfo.sqlite'
    db_filepath = storagepath

    if not os.path.isdir(db_filepath):
        os.makedirs(db_filepath)

    db_filelocation = "%s/%s" % (db_filepath, db_fn)
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
        
    if not SysRef.tableExists():
        SysRef.createTable()

connection = connect()