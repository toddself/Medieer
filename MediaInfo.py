#!/usr/bin/env python
import os, sys
import argparse
from os.path import join as fjoin
import re

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
    title_parser = re.compile('^(.*)\ s(\d+)e(\d+).*$', re.I)    
    
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
        parser.add_argument('--debug', dest='debug', action='store_true', default=False)

        self.options = parser.parse_args(args)

        if self.options.debug:
            print self.options

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
        self.connection = data.connect(self.db_filelocation)

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
        t = api.TMDB()
        genres = t.lookup(domain='genres')
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
        # attempts to store in a site-wide data location.

        # TODO: RE-ENABLE THIS AFTER TESTING
        # try:
        #     os.stat(self.dirs.site_data_dir)
        #     dest_path = self.dirs.site_data_dir            
        # except OSError:
        #     try:
        #         os.makedirs(self.dirs.site_data_dir)
        #         dest_path = self.dirs.site_data_dir
        #     except OSError:
        #         dest_path = self.dirs.user_data_dir
        
        dest_path="/tmp/media_info_testdata"
                
        s = data.Settings(key='dest_path', value=dest_path)
    
        # key: basepath
        # options: any valid directory
        # this option dictates where input files will be found.
        # defaults to the dest_path
        s = data.Settings(key='basepath', value=dest_path)
        
    def exists_in_db(self, videofile):
        try:
            # this means we know about the video, so we can skip querying
            # the apis to find out what video it is.
            if self.options.debug:
                print "Looking up file URI: ", videofile

            self.video = list(data.Media.select(data.Media.q.file_URI==videofile))[0]

            if self.options.debug:
                print "Found video: ", self.video

            self.video_ext = videofile.rsplit('.', 1)[1]
            return True            
            
        except IndexError:
            if self.options.debug:
                print "Video not found"
            
            return False
            
    def lookup_movie(self, video_filename):
        t = api.TMDB(debug=self.options.debug)
        if self.options.debug:
            print "This is a movie, trying to lookup %s via tmdb" % video_filename

        self.results = t.lookup(video_filename)
        
    def lookup_tv(self, video_filename):
        self.results = []
        
    def parse_show_title(self, title_string):
        title_string = title_string.replace('_', ' ')
        try:
            return re.match(self.title_parser, title_string).groups()
        except AttributeError:
            raise AttributeError('%s does not match form of SERIES S?E?' % title_string)        
        
    def resolve_multiple_results(self, video_filename):
        print "Multiple matches were found for %s" % video_filename
        for x in range(len(self.results)):
            print "%s. %s" % (x+1, self.results[x].title)
            
        selection = raw_input('Selection [1]: ')                  
        
        try:
            selected = int(selection)-1
        except ValueError:
            selected = 0
            
        if self.options.debug:
            print "Index selected: ", selected

        return selected
        
    def organize_file(self, videofile):
            self.path = data.get_setting('dest_path')

            if self.options.debug:
                print "Path: ", self.path

            if self.video.media_type.lower() not in self.path:
                self.path = fjoin(self.path, self.video.media_type.lower())
                if self.options.debug:
                    print "Missing media type in path. New path: ", self.path

            if eval(data.get_setting('organize_by_genre').capitalize()):
                self.path = fjoin(self.path, self.video.genres[0].name)
                if self.options.debug:
                    print "Organizing by Genre. New path: ", self.path

            # path determination done, lets make sure it exists
            if not os.path.isdir(self.path):
                try:
                    os.makedirs(self.path)
                except OSError:
                    print "You don't have permissions to write to %" % self.path
                    sys.exit(1)

            if self.options.debug:
                print "Filename: ", self.video.title

            video_destination = fs.generate_filename(self.path, self.video.title, self.video_ext)

            if self.options.debug:
                print "Destination: ", video_destination

            os.rename(videofile, video_destination)

            return video_destination
        
    def generate_image(self):
        try:
            os.stat(self.video.poster_local_URI)
        except OSError:
            poster_dest = fs.generate_filename(self.path, self.video.title, 'jpg')
            try:
                if self.options.debug:
                    print "Source: ", self.video.poster_remote_URI
                    print "Dest: ", poster_dest
                fs.download_file(self.video.poster_remote_URI, poster_dest)
            except OSError:
                print "Can't open %s for writing." % poster_dest
                sys.exit(1)
                
            self.video.poster_local_URI = poster_dest        
    
    def generate_videoxml(self):
        xml_filename = fs.generate_filename(self.path, self.video.title, 'xml')
        try:
            os.stat(xml_filename)
        except OSError:
            x = gen.VideoXML()
            x.makeVideoXML(self.video)
            try:
                with file(xml_filename, 'w') as xf:
                    xf.write(x.toxml)
            except OSError:
                print "Can't open %s for writing." % xml_filename
                sys.exit(1)
    
    def generate_video_directory(self):
        x = gen.VideoXML()
        x.makeVideoDirectory(list(data.Media.select()))
        try:
            output_path = data.get_setting('dest_path')
            with file(fs.generate_filename(output_path, 'video', 'xml'), 'w') as xf:
                xf.write(x.toxml())
        except OSError:
            print "FUCK!"
            sys.exit(1)

    def process_files(self):
        filelist = fs.make_list(fs.get_basepath(data.get_setting('basepath')))
        org_type = data.get_setting('organization_method')
        
        for videofile in filelist:
            if not self.exists_in_db(videofile):
                (path, video_filename, self.video_ext) = fs.fn_to_parts(videofile)
                    
                # what are we looking up? tv? movie?
                if data.Media.media_types[data.Media.MOVIES].lower() in path.lower():
                    self.lookup_movie(video_filename)
                elif data.Media.media_types[data.Media.TV].lower() in path.lower():
                    self.lookup_tv(video_filename)
                else:
                    print "Sorry, I can't figure out how your video files are organized"
                    sys.exit(1)
                    
                # were there multiple results for this?    
                if len(self.results) > 1 and not self.options.first:
                    selected = self.resolve_multiple_results(video_filename)
                    result = self.results[selected]
                    process_vid = True
                elif len(self.results) == 1:
                    result = self.results[0]
                    process_vid = True
                else:
                    if self.options.debug:
                        print "No matches, skipping file"
                    process_vid = False

                if process_vid:
                    if self.options.debug:
                        print "Result: ", result.title                            

                    self.video = data.Media()
                    self.video.fromAPIMedia(result)
            else:
                process_vid = True

            if process_vid:
                # should we organize?
                if self.options.rename:
                    self.video.file_URI = self.organize_file(videofile)
                else:
                    self.video.file_URI = videofile    

                # process the image for the video            
                self.generate_image()

                # process the xml for the video if we're making individual
                # videofiles.  if not, we'll process it all at the end
                if org_type == 'videoxml':
                    self.generate_videoxml()

                try:
                    del self.results
                    del result
                    del self.video
                except AttributeError:
                    pass
    
        # we are going to generate a master video xml file containing all
        # entries
        if org_type == 'directory':
            self.generate_video_directory()

if __name__ == '__main__':
    mi = MediaInfo(sys.argv[1:])