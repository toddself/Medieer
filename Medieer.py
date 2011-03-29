#!/usr/bin/env python
# This file is part of Medieer.
# 
#     Medieer is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Medieer is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import shutil
import argparse
import re
import codecs
import logging
import logging.handlers
from os.path import join as fjoin

from appdirs import AppDirs
from sqlobject.declarative import DeclarativeMeta
from sqlobject import SQLObjectNotFound

import fs, data, gen, api

appname = 'Medieer'
appauthor = 'Todd Kennedy'
authoremail = '<todd.kennedy@gmail.com>'
version = '0.50'

class Medieer():
    #TODO VERSION 1.0: IMPLEMENT GUI
    #TODO VERSION 1.0: IMPLEMENT VERSION MIGRATION
    #TODO VERSION 1++: IMPLEMENT IMDB LOOKUP
    #TODO VERSION 1++: IMPLEMENT TVDB LOOKUP
    #TODO VERSION 1++: ALLOW FOR MULTIPLE CATEGORIZATION -- need to see if symlinks are acceptableT
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
        parser.add_argument('-c', '--change-setting', nargs=1, dest='new_setting', default='',
                help='Change a setting. Example: --change-setting source_path=/etc/videos')
        parser.add_argument('--debug', nargs=1, dest='debug',
                help="Set logging level (most info -> least info)[DEBUG|INFO|WARN|ERROR|CRIT]")
        parser.add_argument('--migrate-database', dest='migrate', action='store_true', 
                default=False, help="Migrate database between versions")

        self.options = parser.parse_args(args)
        self.init_data_dir()
        
        if self.options.debug:
            self.configure_log(self.options.debug[0])
        else:
            self.configure_log('info')

        self.db_filelocation = fjoin(self.dirs.user_data_dir, self.db_fn)
        
        try:
            os.stat(self.db_filelocation)
        except OSError:
            self.logger.info('No db found, assuming fresh install')
            self.init_app()
        
        if not self.connected():
            self.open_db()
            
        # lets figure out what the user wants to do now
        if self.options.show_defaults:
            settings = list(data.Settings.select())
            value_width = max([len(setting.value) for setting in settings])
            key_width = max([len(setting.key) for setting in settings])
            header = "Setting".ljust(key_width)+"\t"+"Value".ljust(value_width)
            print "\n" + header + "\n" + "-" * len("Setting".ljust(key_width)) + "\t" + "-" * len("Value".ljust(value_width))
            for setting in settings:
                print setting.key.ljust(key_width)+"\t"+setting.value.ljust(value_width)
            print
            sys.exit(0)

        if self.options.new_setting:
            (new_key, new_value) = self.options.new_setting[0].split('=')
            try:
                s = list(data.Settings.select(data.Settings.q.key==new_key))[0]
            except IndexError:
                self.logger.critical("%s is not a valid key" % new_key)
                print "%s is not a valid key.  Use --show-defaults to see valid settings to changeself." % new_key
                sys.exit(1)
            else:
                s.value = new_value
                sys.exit(0)

        if self.options.migrate:
            print "Not implemented"
            sys.exit(0)

        if self.options.nogui:
            self.logger.info('No gui passed, processing files')
            self.process_files()
        else:
            self.logger.info('Launching gui')
            self.launch_gui()        
            
    def configure_log(self, level):
        LOG_FILENAME = fjoin(self.dirs.user_data_dir, "%s.log" % appname)
        self.levels = {'debug': logging.DEBUG,
                       'info': logging.INFO,
                       'warn': logging.WARNING,
                       'error': logging.ERROR,
                       'crit': logging.CRITICAL}
               
        self.logger = logging.getLogger(appname)
        log_level = self.levels.get(level.lower(), logging.NOTSET)
        self.logger.setLevel(log_level)
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1024000, backupCount=5)
        handler.setLevel(log_level)
        log_format = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s %(message)s')
        handler.setFormatter(log_format)
        self.logger.addHandler(handler)
    
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
                    self.logger.warning("Can't create: %s" % path)
                    print "Error: can't create %s" % path   
            else:
                path_ready = True
        return path     
        

    def init_data_dir(self):
        # make user data directory
        if not os.path.isdir(self.dirs.user_data_dir):
            try:
                os.makedirs(self.dirs.user_data_dir)
            except OSError:
                print 'Unable to create directory %s. Please verify you have permissions to create this path.' % dirs.user_data_dir
                sys.exit(1)
                
    def init_app(self):        
        # now we can open a connection to the database, creating the file
        # at the same time
        if not self.connected():
            self.open_db()
        
        # make tables
        for cname in dir(data):
            cl = eval('data.%s' % cname)
            if isinstance(cl, DeclarativeMeta):
                if not cl.tableExists():
                    self.logger.info("SETUP: Creating table %s" % cname)
                    cl.createTable()
                    
        # import genre data
        self.logger.info("SETUP: Getting default genre data")
        t = api.TMDB(log=self.logger)
        genres = t.lookup(domain='genres')
        for genre in genres:
            g = data.Genre()
            g.fromAPIGenre(genre)

        # set default settings
        org_method = raw_input('Catalog files by directory or XML Manifest? [XML/dir] ')
        if org_method == '':
            org_method = 'xml'
        master_org = raw_input('Should I organize your files for you? [Y/n] ')
        if master_org == '':
            master_org = 'y'
        movie_genre = raw_input('Do you wish to organize movies by genre? [Y/n] ')
        if movie_genre == '':
            movie_genre = 'y'
        tv_series_genre = raw_input('Should I organize TV by genre? [y/N] ')
        if tv_series_genre == '':
            tv_series_genre = 'n'
        tv_series_org = raw_input('Should I organize television by series and season? [Y/n] ')
        if tv_series_org == '':
            tv_series_org = 'y'
        source_path = self._check_path('Where are your media files located? ', self.dirs.site_data_dir)
        if master_org == 'y':
            dest_path = self._check_path('Where should I place your organized files? ', self.dirs.site_data_dir)
        
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
        # this dictates whether or not Medieer.organize_files() is called
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
            self.logger.debug("Looking up file URI: %s" % videofile)
            self.video = list(data.Media.select(data.Media.q.file_URI==videofile))[0]
            self.logger.debug("Found video: %s" % self.video.title.encode('ascii', 'replace').decode('ascii'))
            self.video_ext = videofile.rsplit('.', 1)[1]
            return True            
            
        except IndexError:
            self.logger.debug("Video not found")
            return False
            
    def lookup_movie(self, video_filename):
        t = api.TMDB(log=self.logger)
        self.logger.debug("This is a movie, trying to lookup %s via tmdb" % video_filename)
        self.results = t.lookup(video_filename)
        
    def lookup_tv(self, video_filename):
        tvr = api.TVRage(log=self.logger)
        self.logger.debug("This is a TV Show, trying to lookup %s via tvrage" % video_filename)
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
            self.logger.info("Sorry, nothing matches series %s" % series_name)
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
            self.logger.warn('%s does not match form of SERIES S?E?' % title_string)        
        
    def resolve_multiple_results(self, video_filename, results):
        print "Multiple matches were found for %s" % video_filename
        for x in range(len(results)):
            print "%s. %s" % (x+1, results[x].title)
            
        selection = raw_input('Selection [1]: ')                  
        
        try:
            selected = int(selection)-1
        except ValueError:
            selected = 0
            
        self.logger.debug("Index selected: %" % selected)

        return selected

    def _make_path(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
                return True
            except OSError:
                self.logger.critical("You don't have permissions to write to %" % path)
                print "You don't have permissions to write to %" % path
                sys.exit(1)
        else:
            return True
        
    def organize_file(self, videofile):
            self.path = data.get_setting('dest_path')
            movies_by_genre = data.get_setting('movies_by_genre')
            tv_by_genre = data.get_setting('tv_series_by_genre')
            tv_by_series = data.get_setting('tv_series_by_series')
            self.logger.debug("Path: %s" % self.path)
            mt = self.video.media_type
            tv = data.media_types[data.TV]
            movies = data.media_types[data.MOVIES]

            if self.video.media_type not in self.path:
                self.path = fjoin(self.path, self.video.media_type)
                self.logger.debug("Missing media type in path. New path: %s" % self.path)
                
            if mt == movies:
                self.logger.debug("MOVIES")
                if movies_by_genre:
                    self.path = fjoin(self.path, self.video.genres[0].name)
                    self.logger.debug("Organizing movies by genre. New path: %s" % self.path)
                        
            elif mt == tv:
                self.logger.debug("TV SHOWS")
                if tv_by_genre:
                    self.path = fjoin(self.path, self.video.genres[0].name)
                    self.logger.debug('Organizing TV by genre. New path: %s' % self.path)
                        
                if tv_by_series:
                    # series level directory
                    self.path = fjoin(self.path, self.video.franchise.name)
                    self._make_path(self.path)
                    if self.org_type == 'videoxml':
                        # for videoxml, the images need to be same name as the
                        # objects they represent
                        (image_path, image_filename) = self.path.rsplit('/',1)
                        image_filename += '.jpg'
                        self.folder_poster = self.generate_image(image_path, image_filename, self.video.franchise.poster_remote_URI)
                    else:
                        self.folder_poster = self.generate_image(self.path, 'poster.jpg', self.video.franchise.poster_remote_URI)
                    self.video.franchise.poster_local_URI = self.folder_poster
                    self.logger.debug("Adding franchise. New path: %s" % self.path)
                    self.logger.debug("Adding poster image %s" % self.folder_poster)
                    
                    # season level directory
                    season = "Season %s" % self.video.season_number
                    self.path = fjoin(self.path, season)
                    self._make_path(self.path)
                    if self.org_type == 'videoxml':
                        image_dest = self.path+".jpg"
                        shutil.copy2(self.video.franchise.poster_local_URI, image_dest)
                    else:
                        shutil.copy2(self.video.franchise.poster_local_URI, self.path)
                    
                    self.logger.debug('Organizing TV by series. New path: %s' % self.path)

            # path determination done, lets make sure it exists
            self._make_path(self.path)
            self.logger.debug("Filename: %s" % self.video.title)
            if self.video.media_type == data.media_types[data.TV]:
                title_filename = "Episode %s: %s" % (self.video.episode_number, self.video.title)
                self.logger.debug('Adding episode number to title: %s' % title_filename)
            else:
                title_filename = self.video.title
            video_destination = fs.generate_filename(self.path, title_filename, self.video_ext)
            self.logger.debug("Destination: %s" % video_destination)
            shutil.move(videofile, video_destination)
            return video_destination
        
    def generate_image(self, local_path, local_title, remote_url):
        local_file = fjoin(local_path, local_title)
        try:
            os.stat(local_file)
        except OSError:
            try:
                self.logger.debug("Source: %s" % remote_url)
                self.logger.debug("Dest: %s" % local_file)
                fs.download_file(remote_url, local_file)
            except OSError:
                self.logger.critical("Can't open %s for writing." % local_file)
                print "Can't open %s for writing." % local_file
                sys.exit(1)
                
            return local_file       
    
    def generate_videoxml(self):
        xml_filename = fs.generate_filename(self.path, self.get_filename_base(self.video.file_URI), 'xml')
        try:
            os.stat(xml_filename)
        except OSError:
            x = gen.VideoXML(log=self.logger)
            x.makeVideoXML(self.video)
            try:
                out = file(xml_filename, 'w')
                out.write(codecs.BOM_UTF8)
                out.write(x.toxml())
                out.close()
            except OSError:
                self.logger.critical("Can't open %s for writing." % xml_filename)
                print "Can't open %s for writing." % xml_filename
                sys.exit(1)
    
    def generate_video_directory(self):
        x = gen.VideoXML(log=self.logger)
        x.makeVideoDirectory(list(data.Media.select()))
        try:
            output_path = data.get_setting('dest_path')
            output_file = fs.generate_filename(output_path, 'video', 'xml')
            out = file(output_file, 'w')
            out.write(codecs.BOM_UTF8)
            out.write(x.toxml())
            out.close()
        except OSError:
            self.logger.critical("Can't open %s for writing." % xml_filename)
            print "Sorry I can't write to %s" % output_path
            sys.exit(1)

    def get_filename_base(self, uri):
        return os.path.split(self.video.file_URI)[1].rsplit('.')[0]

    def process_files(self):
        filelist = fs.make_list(fs.get_basepath(data.get_setting('source_path')))
        self.org_type = data.get_setting('organization_method')
        
        for videofile in filelist:
            if not self.exists_in_db(videofile):
                (path, video_filename, self.video_ext) = fs.fn_to_parts(videofile)
                    
                # what are we looking up? tv? movie?
                if data.Media.media_types[data.Media.MOVIES].lower() in path.lower():
                    self.lookup_movie(video_filename)
                elif data.Media.media_types[data.Media.TV].lower() in path.lower():
                    self.lookup_tv(video_filename)
                else:
                    self.logger.critical("Sorry, I can't figure out how your video files are organized")
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
                    self.logger.debug("No matches, skipping file")
                    process_vid = False

                if process_vid:
                    self.logger.debug("Result: %s" % result.title)

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
                poster_filename = "%s.jpg" % self.get_filename_base(self.video.file_URI)
                if self.video.poster_remote_URI:
                    self.generate_image(self.path, poster_filename, self.video.poster_remote_URI)
                elif self.video.media_type == data.media_types[data.TV] and self.folder_poster:
                    shutil.copy2(self.video.franchise.poster_local_URI, fjoin(self.path, poster_filename))

                # process the xml for the video if we're making individual
                # videofiles.  if not, we'll process it all at the end
                if self.org_type == 'videoxml':
                    self.generate_videoxml()

                try:
                    del self.results
                    del result
                    del self.video
                except AttributeError:
                    pass
    
        # we are going to generate a master video xml file containing all
        # entries
        if self.org_type == 'directory':
            self.generate_video_directory()

if __name__ == '__main__':
    mi = Medieer(sys.argv[1:])
