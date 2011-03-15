#!/usr/bin/env python
import os
import argparse

from appdirs import AppDirs
from sqlobject.declarative import DeclarativeMeta
from sqlobject import SQLObjectNotFound

import io, data, gen, api

__APP_NAME__ = 'MediaInfo'
__APP_AUTHOR__ = 'Todd'
__VERSION__ = '0.10'

class MediaInfo():
    db_fn = '%s.sqlite' % __APP_NAME__
    dirs = AppDirs(__APP_NAME__, __APP_AUTHOR__, version=__VERSION__)
    
    def __init__(self, args):
        parser = argparse.ArgumentParser(description='Manage video metadata.')
        
        # TODO: 
        # CONVERT THE ADD OPTIONS TO ARGPARSE FORMAT
        # ALLOW FOR THE SETTING/CHANGING OF SETTINGS FROM COMMAND LINE
        parser.add_option('-r', '--rename-files', action='store_false', dest='rename', 
                default=True, help='Rename media files to match titles')
        parser.add_option('-n', '--no-gui', action='store_false', dest='nogui', 
                default=True, help="Don't launch GUI; perform XML update via console")
        parser.add_option(-'f', '--choose-first', action='store_true', dest='first',
                default=False, help="If movie matches more than one result, choose first from list.")
        parser.add_option('-d', '--directory', action="store", dest='basepath',
                default='', help='Provide the default directory for video storage.')
        parser.add_option('s', '--show-defaults', action="store_true", dest='show_defaults',
                default=False, help='Show all application settings')
                
        (self.options, self.args) = parser.parse_args()  

        self.db_filelocation = fjoin(self.dirs.user_data_dir, self.db_fn)
        
        if not os.stat(db_filelocation):
            self.init_app()
        
        if not self.connection:
            self.open_db()

        if options.nogui:
            self.process_files()
        else:
            self.launch_gui()        

    def open_db(self):
        self.connection = data.connect(self.db_filelocation)

    def init_app(self):
        # make user data directory
        if not os.path.isdir(dirs.user_data_dir):
            os.makedirs(dirs.user_data_dir)
        
        # now we can open a connection to the database, creating the file
        # at the same time
        if not self.connection:
            self.open_db()
        
        # make tables
        for cname in data:
            cl = eval('data.%s' % cname)
            if isinstance(cl, DeclarativeMeta):
                if not cl.tableExists():
                    cl.createTable()
                    
        # import genre data
        self.t = api.TMDB()
        genres = t.lookup(domain='genres')
        for genre in genres:
            g = data.Genre()
            g.fromAPIGenre(genre)

        # set default settings
        
        # key: organization_method
        # options: directory or videoxml
        # this dictates how file organziation will work, if it's selected
        # and what type of XML file is output by the two default generators
        s = data.Settings(key='organization_method', value='directory') 
        
        # key: basepath
        # options: any valid directory
        # this option determines where the system will check for video files
        # as a default, and to where the additional generated files will be
        # stored.  
        # attempts to store in a site-wide data location.
        os.stat(dirs.site_data_dir)
        try:
            os.makedirs(dirs.site_data_dir)
            basepath = dirs.site_data_dir
        except OSError:
            os.makedirs(dirs.user_data_dir)
            basepath = dirs.user_data_dir
        s = data.Settings(key='basepath', value=basepath)
        

    def process_files(self):
        self.t = api.TMDB()
        filelist = io.make_list(io.get_basepath(data.get_setting('basepath')))
        
        for videofile in filelist:
            try:
                video = data.Media.select(Media.q.file_URI==videofile)
            except SQLObjectNotFound:
                (path, video_filename, ext) = io.fn_to_parts(videofile)    
                movies = t.lookup(video_filename)
                if len(movies) > 1 and not self.options.first:
                    # need to present user with a text-mode choice interface
                    # if more than one movie matches the query
                    pass
                else:
                    movie = movies[0]

                video = data.Media()
                video.fromAPIMedia(movie)
                
                org_type = data.get_setting('organization_method')
                    
                if self.option.rename:
                    video_filename = '%(title)s.%(ext)s' % {'title': video.title, 'ext': ext}
                    os.rename(videofile, io.generate_filename(path, video_filename, ext))
                

                # TODO
                # FINISH FILE PROCESSOR
                # GENERATE XML
                # GRAB POSTER IMAGE
                # UPDATE MEDIA OBJECT
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
            #     self.movie = self.tmdb.getMovieInfoByName(self.movie_fn_base)
            #     if self.options.rename:
            #         self.new_movie_fn_base = self.movie.title
            #         os.rename(fn_video, self.make_filename(self.movie_path, self.new_movie_fn_base, self.movie_fn_extn))
            #         self.movie_fn_base = self.new_movie_fn_base
            # 
            #     self.fn_xml = self.make_filename(self.movie_path, self.movie_fn_base, 'xml')
            #     self.fn_image = self.make_filename(self.movie_path, self.movie_fn_base, 'jpg')            
            # except TMDBNotFoundError:
            #     print self.movie_name, "not found"
            # else:            
            #     if not self.file_exists(self.fn_xml):
            #         if not self.generate_xml():
            #             print "ERROR: Couldn't create file: %s" % self.fn_xml
            #             sys.exit(1)
            #     if not self.file_exists(self.fn_image):
            #         if not self.generate_image():
            #             print "ERROR: Couldn't create file: %s" % self.fn_image
            #             sys.exit(2)            


if __name__ == '__main__':
    mi = MediaInfo()