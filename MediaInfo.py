#!/usr/bin/env python
import os, sys
import argparse
from os.path import join as fjoin

from appdirs import AppDirs
from sqlobject.declarative import DeclarativeMeta
from sqlobject import SQLObjectNotFound

import fs, data, gen, api

appname = 'MediaInfo'
appauthor = 'Todd'
version = '0.10'

class MediaInfo():
    db_fn = '%s.sqlite' % appname
    dirs = AppDirs(appname, appauthor, version=version)
    connection = False
    
    def __init__(self, args):
        parser = argparse.ArgumentParser(description='Manage video metadata.')
        parser.add_argument('-s', '--show-defaults', action="store_true", dest='show_defaults',
                default=False, help='Show all application settings')
        parser.add_argument('-r', '--rename-files', action='store_false', dest='rename', 
                default=True, help='Rename media files to match titles')
        parser.add_argument('-n', '--no-gui', action='store_true', dest='nogui', 
                default=False, help="Don't launch GUI; perform XML update via console")
        parser.add_argument('-f', '--choose-first', action='store_true', dest='first',
                default=False, help="If movie matches more than one result, choose first from list.")       
        parser.add_argument('-d', '--directory', dest='basepath',
                default='', help='Provide the default directory for video storage.')
        parser.add_argument('-c', '--change-setting', dest='settings', default='',
                help='Change a setting. Example: --change-setting basepath=/etc/videos')

        self.options = parser.parse_args()

        self.db_filelocation = fjoin(self.dirs.user_data_dir, self.db_fn)
        
        try:
            os.stat(self.db_filelocation)
        except OSError:
            self.init_app()
        
        if not self.connected():
            self.open_db()

        if self.options.nogui:
            self.process_files()
        else:
            self.launch_gui()        
            
    def connected(self):
        if not self.connection:
            self.open_db()

    def open_db(self):
        self.connection = data.connect(self.db_filelocation, appname)

    def init_app(self):
        # make user data directory
        if not os.path.isdir(self.dirs.user_data_dir):
            try:
                os.makedirs(self.dirs.user_data_dir)
            except OSError:
                print 'Unable to create directory %s. Please verify you have permissions to create this path.' % dirs.user_data_dir
                sys.exit(1)
        
        # now we can open a connection to the database, creating the file
        # at the same time
        if not self.connected():
            self.open_db()
        
        # make tables
        for cname in dir(data):
            cl = eval('data.%s' % cname)
            if isinstance(cl, DeclarativeMeta):
                if not cl.tableExists():
                    cl.createTable()
                    
        # import genre data
        self.t = api.TMDB()
        genres = self.t.lookup(domain='genres')
        for genre in genres:
            g = data.Genre()
            g.fromAPIGenre(genre)

        # set default settings
        
        # key: organization_method
        # options: directory or videoxml
        # this dictates how file organziation will work, if it's selected
        # and what type of XML file is output by the two default generator
        # directory will generate a master xml manifest
        # videoxml will generate a bunch of small files
        s = data.Settings(key='organization_method', value='directory') 
        
        # key: organize_by_genre
        # options: true or false
        # this dictates whether or not videos are located in subdirectories
        # according to genre.  uses the first genre in the list, which
        # we consider to be the 'main' genre
        s = data.Settings(key='organize_by_genre', value='true')
        
        # key: dest_path
        # options: any valid directory
        # this option determines where the system will check for video files
        # as a default, and to where the additional generated files will be
        # stored.  
        # attempts to store in a site-wide data location.'
        try:
            os.stat(self.dirs.site_data_dir)
            dest_path = self.dirs.site_data_dir            
        except OSError:
            try:
                os.makedirs(self.dirs.site_data_dir)
                dest_path = self.dirs.site_data_dir
            except OSError:
                dest_path = self.dirs.user_data_dir
                
        s = data.Settings(key='dest_path', value=dest_path)
    
        # key: basepath
        # options: any valid directory
        # this option dictates where input files will be found.
        # defaults to the dest_path
        s = data.Settings(key='basepath', value=dest_path)
        

    def process_files(self):
        self.t = api.TMDB()
        filelist = fs.make_list(fs.get_basepath(data.get_setting('basepath')))
        org_type = data.get_setting('organization_method')
        
        for videofile in filelist:
            try:
                # this means we know about the video, so we can skip querying
                # the apis to find out what video it is.
                video = data.Media.select(data.Media.q.file_URI==videofile)
            except SQLObjectNotFound:
                (path, video_filename, ext) = fs.fn_to_parts(videofile)
                if data.Media.media_types[data.Media.MOVIES] in path:
                    results = t.lookup(video_filename)
                else:
                    # TODO: TV SHOW API RETRIEVAL
                    # i'm a tv show and i don't know what to do yet!
                    pass
                    
                if len(results) > 1 and not self.options.first:
                    # TODO: SELECTING OPTIONS FROM MULTIMOVIE MATCH
                    # need to present user with a text-mode choice interface
                    # if more than one movie matches the query
                    pass
                else:
                    result = results[0]

                video = data.Media()
                video.fromAPIMedia(result)
                
            
                
            # should we organize?
            if self.options.rename:
                path = data.get_setting('dest_path')
                print video
                if video.media_type.lower() not in path and org_type == 'videoxml':
                    path = fjoin(path, video.media_type.lower())
                    
                if eval(data.get_setting('organize_by_genre').capitalize()):
                    path = fjoin(path, video.genres[0])
                    
                video_filename = video.title
                os.rename(videofile, fs.generate_filename(path, video_filename, ext))
                video.file_URI = fs.generate_filename(path, video_filename, ext)
            else:
                video.file_URI = videofile
            
            # process the image for the video            
            try:
                os.stat(video.poster_local_URI)
            except OSError:
                poster_dest = fs.generate_filename(path, video.title, 'jpg')
                try:
                    fs.download_file(video.poster_local_URI, poster_dest)
                except OSError:
                    print "Can't open %s for writing." % poster_dest
                    sys.exit(1)
                video.poster_local_URI = poster_dest
            except SQLObjectNotFound:
                # TODO: ADD DEFAULT IMAGE FOR GENRE/MEDIA_TYPE
                # there was no image available from the data api so we'll 
                # just skip.
                pass
                

                    
            if org_type == 'videoxml':
                xml_filename = fs.generate_filename(path, video.title, 'xml')
                try:
                    os.stat(xml_filename)
                except OSError:
                    x = gen.VideoXML()
                    x.makeVideoXML(video)
                    try:
                        with file(xml_filename, 'r') as xf:
                            xf.write(x.toxml)
                    except OSError:
                        print "Can't open %s for writing." % xml_filename
                        sys.exit(1)
                    
        if org_type == 'directory' and len(filelist) > 0:
            x = gen.VideoXML()
            x.makeVideoDirectory(list(Media.select()))
            try:
                output_path = data.get_setting('dest_path')
                with file(fs.generate_filename(output_path, 'video', 'xml')) as xf:
                    xf.write(x.toxml())
            except: 
                pass

if __name__ == '__main__':
    mi = MediaInfo(sys.argv[1:])