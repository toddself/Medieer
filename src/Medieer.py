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
__version__ = '0.65'

class Medieer():
    #TODO VERSION 1.0: IMPLEMENT GUI
    #TODO VERSION 1.0: IMPLEMENT VERSION MIGRATION
    #TODO VERSION 1++: IMPLEMENT IMDB LOOKUP
    #TODO VERSION 1++: IMPLEMENT TVDB LOOKUP
    #TODO VERSION 1++: ALLOW FOR MULTIPLE CATEGORIZATION -- need to see if symlinks are acceptable
    #TODO VERSION 1.0 REFACTOR Medieer OBJECT FOR BETTER CODE ORGANIZATION
    db_fn = '%s.sqlite' % appname
    dirs = AppDirs(appname, appauthor)
    connection = False
    title_parser = re.compile('^(.*)\ s(\d+)e(\d+).*$', re.I)    
    
    def __init__(self, args):
        parser = argparse.ArgumentParser(description='Manage media metadata.')
        parser.add_argument('-s', '--show-defaults', action="store_true", dest='show_defaults',
                default=False, help='Show all application settings')
        parser.add_argument('-n', '--no-gui', action='store_true', dest='nogui', 
                default=False, help="Don't launch GUI; perform XML update via console")
        parser.add_argument('-f', '--choose-first', action='store_true', dest='first',
                default=False, help="If movie matches more than one result, choose first from list.")      
        parser.add_argument('--rewind', action='store_true', dest='rewind',
                default=False, help="Return videos to original destinations and delete metadata.")
        parser.add_argument('-c', '--change-setting', nargs=1, dest='new_setting', default='',
                help='Change a setting. Example: --change-setting source_path=/etc/videos')
        parser.add_argument('--debug', nargs=1, dest='debug',
                help="Set logging level (most info -> least info)[DEBUG|INFO|WARN|ERROR|CRIT]")
        parser.add_argument('-x', '--regenerate-xml', dest='regenerate_xml', default=False,
                action='store_true', help='Generate XML from data in database.  Do not process new files.')

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
            self.show_defaults()

        if self.options.new_setting:
            self.change_setting(self.options.new_setting)
            
        if self.options.rewind:
            confirm = raw_input(
"""Are you sure you want to revert?
Your files will be moved back to the original locations and renamed. 
Nothing else will be done. [y/N]""")
            if confirm.lower() == 'y':
                self.logger.info('Rewinding!')
                self.rewind()
                sys.exit(0)
            else:
                print "Nothing changed."
                sys.exit(0)

        if self.options.regenerate_xml:
            self.logger.info('Regenerating XML')
            videos = list(data.Media.select())
            self.logger.debug('Org method: %s ' % data.get_setting('organization_method'))
            if data.get_setting('organization_method') == 'videoxml':
                self.logger.info('Video org method is videoxml')
                for video in videos:
                    self.logger.debug('Regenerating for %s' % video.title)
                    self.generate_videoxml(os.path.split(video.file_URI)[0], video)
            else:
                self.logger.info('Video org method is directory')
                self.generate_video_directory()
            sys.exit(0)

        if self.options.nogui:
            self.logger.info('No gui passed, processing files')
            self.process_files()
        else:
            self.logger.info('Launching gui')
            self.launch_gui()
    
    def rewind(self):
        try:
            media = list(data.Media.select())
        except SQLObjectNotFound:
            msg = 'No media found with which to rewind'
            self.logger.info(msg)
            print msg
            sys.exit(0)
        else:                
            for medium in media:
                if medium.file_URI:                    
                    if medium.original_file_URI:
                        self.logger.debug('Original file location exists')
                        self.logger.info('Moving: %s to %s' % (medium.file_URI, medium.original_file_URI))
                        shutil.move(medium.file_URI, medium.original_file_URI)
                    else:
                        self.logger.debug('Original file location does not exist')
                        source_path = data.get_setting('source_path')
                        media_directory = medium.media_type
                        try:
                            self.logger.debug("Franchise name: %s" % medium.franchise.name)
                            new_title = medium.franchise.name
                        except SQLObjectNotFound:
                            self.logger.debug('Franchise has no name: %s' % medium.title)                            
                            new_title = medium.title
                        
                        if medium.media_type == data.media_types[data.TV]:
                            filename = '%s S%sE%s.%s' % (new_title, 
                                                        medium.season_number,
                                                        medium.episode_number,
                                                        medium.codec)
                        else:
                            filename = '%s.%s' % (new_title, medium.codec)
                            
                        self.logger.debug(filename)
                        dest = fjoin(source_path, media_directory, filename)
                        self.logger.info('Moving: %s to %s' % (medium.file_URI, dest))
                        shutil.move(medium.file_URI, dest)
                        medium.file_URI = dest
                else:
                    msg = 'This medium does not exist. Got empty location. %s' % medium.title
                    self.logger.error(msg)
    
    def change_setting(self, new_setting):
        try:
            split = new_setting[0].index('=')
            new_key = new_setting[0][:split]
            new_value = new_setting[0][split+1:]
        except IndexError:
            msg = 'Missing setting'
            self.logger.critical(msg)
            print msg
            sys.exit(1)
        except ValueError:
            msg = '%s is not in the form of key=value.' % new_setting[0]
            self.logger.critical(msg)
            print msg
            sys.exit(1)
        else:
            try:
                s = list(data.Settings.select(data.Settings.q.key==new_key))[0]
            except IndexError:
                self.logger.critical("%s is not a valid key" % new_key)
                print "%s is not a valid key.  Use --show-defaults to see valid settings to change." % new_key
                sys.exit(1)
            else:
                s.value = new_value
                msg = 'Changed key %s to value %s' % (s.key, s.value)
                self.logger.info(msg)
                print msg
                sys.exit(0)
    
    def show_defaults(self):
        settings = list(data.Settings.select())
        value_width = max([len(setting.value) for setting in settings])
        key_width = max([len(setting.key) for setting in settings])
        header = "Setting".ljust(key_width)+"\t"+"Value".ljust(value_width)
        print "\n" + header
        print "-" * len("Setting".ljust(key_width)) + "\t" + "-" * len("Value".ljust(value_width))
        for setting in settings:
            print setting.key.ljust(key_width)+"\t"+setting.value.ljust(value_width)
        print
        sys.exit(0)        
    
    def configure_log(self, level):
        LOG_FILENAME = fjoin(self.dirs.user_data_dir, "%s.log" % appname)
        levels = {'debug': logging.DEBUG,
                       'info': logging.INFO,
                       'warn': logging.WARNING,
                       'error': logging.ERROR,
                       'crit': logging.CRITICAL}
                       
        logging.basicConfig(level = levels.get(level, logging.NOTSET),
                                 format = '[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s',
                                 datefmt = '%m/%d %H:%M',
                                 filename=LOG_FILENAME,
                                 filemode='w')
        self.logger = logging.getLogger('')
    
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
                else:
                    # TODO: Add the ability to add columns if necessary
                    passT
                    
        # import genre data
        self.logger.info("SETUP: Getting default genre data")
        t = api.TMDB(log=logging.getLogger('TMDB'))
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
        
    # TODO: REFACTOR BELOW OUT INTO A NEW MODULE
    def exists_in_db(self, videofile):
        self.logger.debug("Looking up file URI: %s" % videofile)
        try:
            self.video = list(data.Media.select(data.Media.q.file_URI==videofile))[0]
        except IndexError:
            try:
                self.video = list(data.Media.select(data.Media.q.original_file_URI==videofile))[0]
            except IndexError:
                self.logger.debug('Video not found')
                return False
        else:
            self.logger.debug("Found video: %s" % self.video.title.encode('ascii', 'replace').decode('ascii'))
            self.video_ext = videofile.rsplit('.', 1)[1]
            return True
            
    def lookup_movie(self, video_filename):
        t = api.TMDB(log=logging.getLogger('TMDB'))
        self.logger.debug("This is a movie, trying to lookup %s via tmdb" % video_filename)
        self.results = t.lookup(video_filename)
        
    def lookup_tv(self, video_filename):
        tvr = api.TVRage(log=logging.getLogger('TVRage'))
        self.logger.debug("This is a TV Show, trying to lookup %s via tvrage" % video_filename)
        (series_name, season, episode) = self.parse_show_title(video_filename)
        series = self.get_series(series_name, tvr, video_filename)
        self.results = tvr.lookup(series_id=series.get_tvrage_series_id(), season=season, episode=episode)
        
    def get_series(self, series_name, tvr, video_filename):
        # lets see if this series exists
        lookup_name = series_name.replace('.', ' ').replace('_', ' ')[:8]
        series = list(data.Series.select(data.Series.q.name.startswith(lookup_name)))
        
        if len(series) == 0:
            self.logger.debug('Nothing starting with %s, looking up: %s' % (lookup_name, series_name))
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
            
    def clean_name_for_fs(self, name):
        return name.replace('(', '').replace(')', '').replace(':','')
        
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
                    self.path = fjoin(self.path, self.clean_name_for_fs(self.video.genres[0].name))
                    self.logger.debug("Organizing movies by genre. New path: %s" % self.path)
                        
            elif mt == tv:
                self.logger.debug("TV SHOWS")
                if tv_by_genre:
                    self.path = fjoin(self.path, self.clean_name_for_fs(self.video.genres[0].name))
                    self.logger.debug('Organizing TV by genre. New path: %s' % self.path)
                        
                if tv_by_series:
                    # series level directory
                    self.path = fjoin(self.path, self.clean_name_for_fs(self.video.franchise.name))
                    self._make_path(self.path)
                    if self.org_type == 'videoxml':
                        # for videoxml, the images need to be same name as the
                        # objects they represent
                        (image_path, image_filename) = self.path.rsplit('/',1)
                        image_filename += '.jpg'
                        self.folder_poster = self.generate_image(image_path, image_filename, self.video.franchise.poster_remote_URI)
                        self.logger.debug("Local poster URI: %s" % self.folder_poster)
                        self.video.franchise.poster_local_URI = self.folder_poster
                    else:
                        self.folder_poster = self.generate_image(self.path, 'poster.jpg', self.video.franchise.poster_remote_URI)
                        self.logger.debug("Local poster URI: %s" % self.folder_poster)                        
                        self.video.franchise.poster_local_URI = self.folder_poster
                        
                    self.logger.debug("Adding franchise. New path: %s" % self.path)
                    self.logger.debug("Adding poster image %s" % self.folder_poster)
                    
                    # season level directory
                    season = "Season %s" % self.video.season_number
                    self.path = fjoin(self.path, season)
                    self._make_path(self.path)
                    if self.org_type == 'videoxml':
                        image_dest = self.path+".jpg"
                        self.logger.debug("Franchise: %s" % self.video.franchise)
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
        else:
            return local_file
    
    def generate_videoxml(self, path, video):
        xml_filename = fs.generate_filename(path, self.get_filename_base(video.file_URI), 'xml')
        x = gen.VideoXML(log=logging.getLogger('VideoXML'))
        x.makeVideoXML(video)
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
        x = gen.VideoXML(log=logging.getLogger('VideoXML'))
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
        return os.path.split(uri)[1].rsplit('.')[0]
        
    def process_files(self):
        filelist = fs.make_list(fs.get_basepath(data.get_setting('source_path')))
        self.org_type = data.get_setting('organization_method')
        
        for videofile in filelist:
            original_file_location = videofile
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
                    self.video.original_file_URI = original_file_location
                else:
                    self.video.file_URI = videofile
                    self.video.original_file_URI = videofile

                # process the image for the video
                poster_filename = "%s.jpg" % self.get_filename_base(self.video.file_URI)
                if self.video.poster_remote_URI:
                    self.generate_image(self.path, poster_filename, self.video.poster_remote_URI)
                elif self.video.media_type == data.media_types[data.TV] and self.folder_poster:
                    shutil.copy2(self.video.franchise.poster_local_URI, fjoin(self.path, poster_filename))

                # process the xml for the video if we're making individual
                # videofiles.  if not, we'll process it all at the end
                if self.org_type == 'videoxml':
                    self.generate_videoxml(self.path, self.video)

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
