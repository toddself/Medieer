#!/usr/bin/env python
import os
import sys
import shutil
import argparse
import re
import codecs
from os.path import join as fjoin

from appdirs import AppDirs
from sqlobject.declarative import DeclarativeMeta
from sqlobject import SQLObjectNotFound

import fs, data, gen, api

appname = 'MediaInfo'
appauthor = 'Todd'
version = '0.10'

class MediaInfo():
    #TODO: ENABLE ABILITY TO SHOW/SET ATTRIBUTES
    #TODO: IMPLEMENT PYTHON LOGGING INSTEAD OF DEBUG PRINTING
    #TODO: IMPLEMENT GUI
    db_fn = '%s.sqlite' % appname
    dirs = AppDirs(appname, appauthor, version=version)
    connection = False
    title_parser = re.compile('^(.*)\ s(\d+)e(\d+).*$', re.I)    
    
    def __init__(self, args):
        parser = argparse.ArgumentParser(description='Manage video metadata.')
        parser.add_argument('-s', '--show-defaults', action="store_true", dest='show_defaults',
                default=False, help='Show all application settings')
        parser.add_argument('-n', '--no-gui', action='store_true', dest='nogui', 
                default=False, help="Don't launch GUI; perform XML update via console")
        parser.add_argument('-f', '--choose-first', action='store_true', dest='first',
                default=False, help="If movie matches more than one result, choose first from list.")       
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
        
    def _check_path(self, question, path):
        path_ready = False
        while not path_ready:
            path = raw_input("%s [%s]" % (question, path))
            try:
                os.stat(path)
            except OSError:
                try:
                    os.makedirs(path)
                    path_ready = True
                except OSError:
                    print "Error: can't create %s" % path   
            else:
                path_ready = True
        return path     
        

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
        org_method = raw_input('Catalog files by directory or XML Manifest? [DIR/xml]')
        if org_method == '':
            org_method = 'dir'
        master_org = raw_input('Should I organize your files for you? [Y/n]')
        if master_org == '':
            master_org = 'y'
        movie_genre = raw_input('Do you wish to organize movies by genre? [Y/n]')
        if movie_genre == '':
            movie_genre = 'y'
        tv_series_genre = raw_input('Should I organize TV by genre? [y/N]')
        if tv_series_genre == '':
            tv_series_genre = 'n'
        tv_series_org = raw_input('Should I organize television by series and season? [Y/n]')
        if tv_series_org == '':
            tv_series_org = 'y'
        source_path = self._check_path('Where are your media files located?', self.dirs.site_data_dir)
        if master_org == 'y':
            dest_path = self._check_path('Where should I place your organized files', self.dirs.site_data_dir)
        
        # key: organization_method
        # options: directory or videoxml
        # this dictates how file organziation will work, if it's selected
        # and what type of XML file is output by the two default generator
        # directory will generate a master xml manifest
        # videoxml will generate a bunch of small files
        if org_method == 'dir':
            s = data.Settings(key='organization_method', value='directory') 
        else:
            s = data.Settings(key='organization_method', value='videoxml')
        
        # key: master_org
        # options: true or false
        # this dictates whether or not MediaInfo.organize_files() is called
        if master_org == 'y':
            s = data.Settings(key='master_org', value='true')
        else:
            s = data.Settings(key='master_org', value='false')
        
        # key: movies_by_genre
        # options: true or false
        # this dictates whether or not movies are located in subdirectories
        # according to genre.  uses the first genre in the list, which
        # we consider to be the 'main' genre
        if movie_genre == 'y':
            s = data.Settings(key='movies_by_genre', value='true')
        else:
            s = data.Settings(key='movies_by_genre', value='false')
            
        # key: tv_series_by_genre
        # options: true or false
        if tv_series_genre == 'y':
            s = data.Settings(key='tv_series_by_genre', value='true')
        else:
            s = data.Settings(key='tv_series_by_genre', value='false')
    
        # key: tv_series_org
        # options: true or false
        if tv_series_org == 'y':
            s = data.Settings(key='tv_series_by_series', value='true')
        else:
            s = data.Settings(key='tv_series_by_series', value='false')
        
        # key: dest_path
        # options: any valid directory
        # this option determines where the system will check for video files
        # as a default, and to where the additional generated files will be
        # stored.            
        s = data.Settings(key='dest_path', value=dest_path)
    
        # key: basepath
        # options: any valid directory
        # this option dictates where input files will be found.
        # defaults to the dest_path
        s = data.Settings(key='source_path', value=source_path)
        
    def exists_in_db(self, videofile):
        try:
            # this means we know about the video, so we can skip querying
            # the apis to find out what video it is.
            if self.options.debug:
                print "Looking up file URI: ", videofile

            self.video = list(data.Media.select(data.Media.q.file_URI==videofile))[0]

            if self.options.debug:
                print "Found video: ", self.video.encode('ascii', 'replace').decode('ascii')

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
        tvr = api.TVRage(debug=self.options.debug)
        if self.options.debug:
            print "This is a TV Show, trying to lookup %s via tvrage" % video_filename
            
        (series_name, season, episode) = self.parse_show_title(video_filename)
        
        series = self.get_series(series_name, tvr, video_filename)

        self.results = tvr.lookup(series_id=series.get_tvrage_series_id(), season=season, episode=episode)
        
    def get_series(self, series_name, tvr, video_filename):
        # lets see if this series exists
        lookup_name = series_name.replace('.', ' ').replace('_', ' ')[:8]
        series = list(data.Series.select(data.Series.q.name.startswith(lookup_name)))
        
        if len(series) == 0:
            series = tvr.lookup(title=series_name)
        
        if self.options.first:
            selected_series = series[0]
        
        if len(series) > 1 and not self.options.first:
            selected_series = series[self.resolve_multiple_results(video_filename, series)]
        elif len(series) == 1 or self.options.first:
            selected_series = series[0]
        else:
            print "Sorry, nothing matches series %s" % series_name
            
        if not isinstance(selected_series, data.Series):
            s = data.Series()
            s.fromAPISeries(selected_series)
            selected_series = s

        return selected_series
        
    def parse_show_title(self, title_string):
        title_string = title_string.replace('_', ' ').replace('.', ' ')
        try:
            return re.match(self.title_parser, title_string).groups()
        except AttributeError:
            raise AttributeError('%s does not match form of SERIES S?E?' % title_string)        
        
    def resolve_multiple_results(self, video_filename, results):
        print "Multiple matches were found for %s" % video_filename
        for x in range(len(results)):
            print "%s. %s" % (x+1, results[x].title)
            
        selection = raw_input('Selection [1]: ')                  
        
        try:
            selected = int(selection)-1
        except ValueError:
            selected = 0
            
        if self.options.debug:
            print "Index selected: ", selected

        return selected

    def _make_path(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
                return True
            except OSError:
                print "You don't have permissions to write to %" % path
                sys.exit(1)
        else:
            return True
        
    def organize_file(self, videofile):
            self.path = data.get_setting('dest_path')
            movies_by_genre = data.get_setting('movies_by_genre')
            tv_by_genre = data.get_setting('tv_series_by_genre')
            tv_by_series = data.get_setting('tv_series_by_series')
            
            if self.options.debug:
                print "Path: ", self.path

            if self.video.media_type.lower() not in self.path:
                self.path = fjoin(self.path, self.video.media_type.lower())
                if self.options.debug:
                    print "Missing media type in path. New path: ", self.path
                
            if self.video.media_type == data.media_types[data.MOVIES]:
                if self.options.debug:
                    print "MOVIES"
                if movies_by_genre:
                    self.path = fjoin(self.path, self.video.genres[0].name)
                    if self.options.debug:
                        print "Organizing movies by genre. New path: ", self.path
                        
            elif self.video.media_type == data.media_types[data.TV]:
                if self.options.debug:
                    print "TV SHOWS"
                if tv_by_genre:
                    self.path = fjoin(self.path, self.video.genres[0].name)
                    if self.options.debug:
                        print 'Organizing TV by genre. New path: ', self.path
                        
                if tv_by_series:
                    # series level directory
                    self.path = fjoin(self.path, self.video.franchise.name)
                    self._make_path(self.path)
                    self.folder_poster = self.generate_image(self.path, 'poster.jpg', self.video.franchise.poster_remote_URI)
                    if self.options.debug:
                        print "Adding franchise. New path: ", self.path
                    
                    # season level directory
                    season = "season %s" % self.video.season_number
                    self.path = fjoin(self.path, season)
                    self._make_path(self.path)
                    if self.folder_poster:
                        shutil.copy2(self.folder_poster, self.path)
                    
                    if self.options.debug:
                        print 'Organizing TV by series. New path: ', self.path

            # path determination done, lets make sure it exists
            self._make_path(self.path)

            if self.options.debug:
                print "Filename: ", self.video.title

            video_destination = fs.generate_filename(self.path, self.video.title, self.video_ext)

            if self.options.debug:
                print "Destination: ", video_destination

            shutil.move(videofile, video_destination)

            return video_destination
        
    def generate_image(self, local_path, local_title, remote_url):
        local_file = fjoin(local_path, local_title)
        try:
            os.stat(local_file)
        except OSError:
            try:
                if self.options.debug:
                    print "Source: ", remote_url
                    print "Dest: ", local_file
                fs.download_file(remote_url, local_file)
            except OSError:
                print "Can't open %s for writing." % local_file
                sys.exit(1)
                
            return local_file       
    
    def generate_videoxml(self):
        xml_filename = fs.generate_filename(self.path, self.video.title, 'xml')
        try:
            os.stat(xml_filename)
        except OSError:
            x = gen.VideoXML()
            x.makeVideoXML(self.video)
            try:
                out = file(xml_filename, 'w')
                out.write(codecs.BOM_UTF8)
                out.write(x.toxml())
                out.close()
            except OSError:
                print "Can't open %s for writing." % xml_filename
                sys.exit(1)
    
    def generate_video_directory(self):
        x = gen.VideoXML()
        x.makeVideoDirectory(list(data.Media.select()))
        try:
            output_path = data.get_setting('dest_path')
            output_file = fs.generate_filename(output_path, 'video', 'xml')
            out = file(output_file, 'w')
            out.write(codecs.BOM_UTF8)
            out.write(x.toxml())
            out.close()
        except OSError:
            print "Sorry I can't write to %s" % output_path
            sys.exit(1)

    def process_files(self):
        filelist = fs.make_list(fs.get_basepath(data.get_setting('source_path')))
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
                    selected = self.resolve_multiple_results(video_filename, self.results)
                    result = self.results[selected]
                    process_vid = True
                elif len(self.results) == 1 or self.options.first:
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
                if data.get_setting('master_org'):
                    self.video.file_URI = self.organize_file(videofile)
                else:
                    self.video.file_URI = videofile    

                # process the image for the video
                poster_filename = "%s.jpg" % self.video.title
                if self.video.poster_remote_URI:
                    self.generate_image(self.path, poster_filename, self.video.poster_remote_URI)
                elif self.video.media_type == data.media_types[data.TV] and self.folder_poster:
                    shutil.copy2(self.folder_poster, fjoin(self.path, poster_filename))
                    

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