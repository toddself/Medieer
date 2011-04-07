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
#     along with Medieer.  If not, see <http://www.gnu.org/licenses/>.

import logging
import string
import unicodedata
import codecs
import re
from os.path import join as fjoin

from pubsub import pub
from sqlobject import SQLObjectNotFound

from core.models import Media, get_setting, media_in_db
from lib.generators import *

VALID_FILENAME_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
TITLE_PARSER = re.compile('^(.*)s(\d+)e(\d+).*$', re.I) 

def create_safe_filename(self, filename):
    dfn = unicodedata.normalize('NFKD', filename).encode('ASCII','ignore')
    return ''.join([c for c in dfn if c in VALID_FILENAME_CHARS])

class FileTools():
    
    def __init__(self):
        pub.subscribe(self.rewind, 'REWIND')
        pub.subscribe(self.generate_xml, 'GENERATE_XML')
        pub.subscribe(self.process_file, 'PROCESS_FILE')
        pub.subscribe(self.output_xml, 'OUTPUT_XML')
        self.log = logging.getLogger('filetools')
        self.output = []
        
    def rewind(self):
        try:
            media = list(Media.select())
        except SQLObjectNotFound:
            msg = 'No media found with which to rewind'
            log.info(msg)
            sys.exit(msg)
        else:                
            for medium in media:
                if medium.file_URI:                    
                    if medium.original_file_URI:
                        log.debug('Moving: %s to %s' % (medium.file_URI, 
                                                    medium.original_file_URI))
                        shutil.move(medium.file_URI, medium.original_file_URI)
                    else:
                        log.debug('Original file location does not exist')
                        source_path = data.get_setting('source_path')
                        media_directory = medium.media_type
                        try:
                            log.debug("Franchise: %s" % medium.franchise.name)
                            new_title = medium.franchise.name
                        except SQLObjectNotFound:
                            log.debug('No franchise: %s' % medium.title)                            
                            new_title = medium.title
                        if medium.media_type == data.media_types[data.TV]:
                            filename = '%s S%sE%s.%s' % (new_title, 
                                                        medium.season_number,
                                                        medium.episode_number,
                                                        medium.codec)
                        else:
                            filename = '%s.%s' % (new_title, medium.codec)
                        dest = fjoin(source_path, media_directory, filename)
                        log.debug('Moving: %s to %s' % (medium.file_URI, dest))
                        shutil.move(medium.file_URI, dest)
                        medium.file_URI = dest
                else:
                    msg = "%s can't be rewound." % medium.title
                    log.error(msg)
                    pub.sendMessage('STD_OUT', msg=msg)

    def process_file(self, filename):
        if not media_in_db(filename):
            

    def generate_xml(self, media_file_URI):
        # TODO: MASSIVE REFACTORING IN OUTPUT!!!
        try:
            media = list(Media.select(Media.q.file_URI==media_file_URI))[0]
        except IndexError:
            msg = '%s is not found' % media_file_URI
            pub.sendMessage('STD_OUT', msg)
        else:
            self.generator_type = get_setting('output_type')
            try:
                generator = eval(self.generator_type)(media)
            except NameError:
                msg = '%s generator not available.' % generator_type
                pub.sendMessage('STD_OUT', msg)
            else:
                self.output.append(generator)
    
    def output_xml(self):
        try:
            if self.output[0].output_type == self.output.SINGLE_FILE:
                data = self.output[0].xml_open()
                for out in self.output:
                    data += out.item_to_xml()
                data += self.output[0].xml_close()
                output_filename = get_settings('output_file')
                self.write_to_disk(output_filename, data)
            else:
                for out in self.output:
                    self.write_to_disk(out.filename, out.item_to_xml())
        except IndexError:
            msg = '%s no data to write'
            pub.sendMessage(msg)
            
    def write_to_disk(self, filename, data):
        try:
            fh = file(filename, 'w')
            if isinstance(data, str) or isinstance(data, unicode):
                fh.write(codecs.BOM_UTF8)
            fh.write(data)
            out.close()
        except OSError:
            msg = "Can't open %s for writing" % filename
            pub.sendMessage(msg)







               



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
                    log.warning("Can't create: %s" % path)
                    print "Error: can't create %s" % path   
            else:
                path_ready = True
        return path     




    # TODO: REFACTOR BELOW OUT INTO A NEW MODULE

    def lookup_movie(self, video_filename):
        t = api.TMDB(log=logging.getLogger('TMDB'))
        log.debug("This is a movie, trying to lookup %s via tmdb" % video_filename)
        self.results = t.lookup(video_filename)

    def lookup_tv(self, video_filename):
        tvr = api.TVRage(log=logging.getLogger('TVRage'))
        log.debug("This is a TV Show, trying to lookup %s via tvrage" % video_filename)
        (series_name, season, episode) = self.parse_show_title(video_filename)
        series = self.get_series(series_name, tvr, video_filename)
        self.results = tvr.lookup(series_id=series.get_tvrage_series_id(), season=season, episode=episode)

    def get_series(self, series_name, tvr, video_filename):
        # lets see if this series exists
        lookup_name = series_name.replace('.', ' ').replace('_', ' ')[:8]
        series = list(data.Series.select(data.Series.q.name.startswith(lookup_name)))

        if len(series) == 0:
            log.debug('Nothing starting with %s, looking up: %s' % (lookup_name, series_name))
            series = tvr.lookup(title=series_name)

        if self.options.first:
            selected_series = series[0]

        if len(series) > 1 and not self.options.first:
            selected_series = series[self.resolve_multiple_results(video_filename, series)]
        elif len(series) == 1 or self.options.first:
            selected_series = series[0]
        else:
            log.info("Sorry, nothing matches series %s" % series_name)
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
            log.warn('%s does not match form of SERIES S?E?' % title_string)        

    def resolve_multiple_results(self, video_filename, results):
        print "Multiple matches were found for %s" % video_filename
        for x in range(len(results)):
            print "%s. %s" % (x+1, results[x].title)

        selection = raw_input('Selection [1]: ')                  

        try:
            selected = int(selection)-1
        except ValueError:
            selected = 0

        log.debug("Index selected: %" % selected)

        return selected

    def _make_path(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
                return True
            except OSError:
                log.critical("You don't have permissions to write to %" % path)
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
            log.debug("Path: %s" % self.path)
            mt = self.video.media_type
            tv = data.media_types[data.TV]
            movies = data.media_types[data.MOVIES]

            if self.video.media_type not in self.path:
                self.path = fjoin(self.path, self.video.media_type)
                log.debug("Missing media type in path. New path: %s" % self.path)

            if mt == movies:
                log.debug("MOVIES")
                if movies_by_genre:
                    self.path = fjoin(self.path, self.clean_name_for_fs(self.video.genres[0].name))
                    log.debug("Organizing movies by genre. New path: %s" % self.path)

            elif mt == tv:
                log.debug("TV SHOWS")
                if tv_by_genre:
                    self.path = fjoin(self.path, self.clean_name_for_fs(self.video.genres[0].name))
                    log.debug('Organizing TV by genre. New path: %s' % self.path)

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
                        log.debug("Local poster URI: %s" % self.folder_poster)
                        self.video.franchise.poster_local_URI = self.folder_poster
                    else:
                        self.folder_poster = self.generate_image(self.path, 'poster.jpg', self.video.franchise.poster_remote_URI)
                        log.debug("Local poster URI: %s" % self.folder_poster)                        
                        self.video.franchise.poster_local_URI = self.folder_poster

                    log.debug("Adding franchise. New path: %s" % self.path)
                    log.debug("Adding poster image %s" % self.folder_poster)

                    # season level directory
                    season = "Season %s" % self.video.season_number
                    self.path = fjoin(self.path, season)
                    self._make_path(self.path)
                    if self.org_type == 'videoxml':
                        image_dest = self.path+".jpg"
                        log.debug("Franchise: %s" % self.video.franchise)
                        shutil.copy2(self.video.franchise.poster_local_URI, image_dest)
                    else:
                        shutil.copy2(self.video.franchise.poster_local_URI, self.path)

                    log.debug('Organizing TV by series. New path: %s' % self.path)

            # path determination done, lets make sure it exists
            self._make_path(self.path)
            log.debug("Filename: %s" % self.video.title)
            if self.video.media_type == data.media_types[data.TV]:
                title_filename = "Episode %s: %s" % (self.video.episode_number, self.video.title)
                log.debug('Adding episode number to title: %s' % title_filename)
            else:
                title_filename = self.video.title
            video_destination = fs.generate_filename(self.path, title_filename, self.video_ext)
            log.debug("Destination: %s" % video_destination)
            shutil.move(videofile, video_destination)
            return video_destination

    def generate_image(self, local_path, local_title, remote_url):
        local_file = fjoin(local_path, local_title)
        try:
            os.stat(local_file)
        except OSError:
            try:
                log.debug("Source: %s" % remote_url)
                log.debug("Dest: %s" % local_file)
                fs.download_file(remote_url, local_file)
            except OSError:
                log.critical("Can't open %s for writing." % local_file)
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
            log.critical("Can't open %s for writing." % xml_filename)
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
            log.critical("Can't open %s for writing." % xml_filename)
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
                    log.critical("Sorry, I can't figure out how your video files are organized")
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
                    log.debug("No matches, skipping file")
                    process_vid = False

                if process_vid:
                    log.debug("Result: %s" % result.title)

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

def main(options, log):
    console = Console(options, log)

if __name__ == '__main__':
    mi = Medieer(sys.argv[1:])
