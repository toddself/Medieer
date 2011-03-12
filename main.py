#!/usr/bin/env python
import os
import sys
import codecs
from os.path import join as fjoin
from urllib2 import urlopen

import data
from api import TMDB
from gen import VideoXML

__APP_NAME__ = 'MediaInfo'
__APP_AUTHOR__ = 'Todd'
__VERSION__ = '0.10'

class GenerateXML():
    videos = []
    allowed_extensions = ['m4v', 'mp4', 'mov', 'wmv']
    allowed_types = ['VideoXML']

    def __init__(self, basepath, options, xml_type="VideoXML"):
        self.videos = self.get_video_filelist(basepath)
        self.options = options

        if xml_type in self.allowed_xml_types:
            self.xml_type = xml_type

        self.process()    

    def get_video_filelist(self, basepath):
        for root, dirs, files in os.walk(basepath):
            for name in files:
                if name.split('.')[-1] in self.allowed_extensions:
                    self.videos.append(fjoin(root,name))

        return self.videos

    def file_exists(self, fn):
        try:
            os.stat(fn)
        except OSError:
            return False
        else:
            return True

    def generate_xml(self):
        try:
            out = file(self.fn_xml, 'w')
            out.write(codecs.BOM_UTF8)
            out.write(self.movie.toxml().encode('utf-8'))
            out.close()
        except OSError:
            return False
        else:
            return True

    def generate_image(self):
        if len(self.movie.poster_remote_URI) < 1:
            return False
        try:
            fh = open(self.fn_image, 'wb')
            fh.write(urlopen(self.movie.poster_remote_URI).read())
            fh.close()
        except OSError:
            return False
        else:
            return True

    def make_filename(self, movie_path, movie_name, extn):
        return fjoin(movie_path, "%s.%s" % (movie_name, extn))

    def process(self):
        for fn_video in self.videos:
            self.tmdb = TMDB()
            if self.tmdb.genreCount() == 0:
                self.tmdb.populateGenres()

            (self.movie_path, self.movie_fn) = fn_video.rsplit('/', 1)
            (self.movie_fn_base, self.movie_fn_extn) = self.movie_fn.rsplit('.', 1)
            self.movie_name = self.movie_fn_base.replace('_', ' ')
            try:
                self.movie = self.tmdb.getMovieInfoByName(self.movie_fn_base)
                if self.options.rename:
                    self.new_movie_fn_base = self.movie.title
                    os.rename(fn_video, self.make_filename(self.movie_path, self.new_movie_fn_base, self.movie_fn_extn))
                    self.movie_fn_base = self.new_movie_fn_base

                self.fn_xml = self.make_filename(self.movie_path, self.movie_fn_base, 'xml')
                self.fn_image = self.make_filename(self.movie_path, self.movie_fn_base, 'jpg')            
            except TMDBNotFoundError:
                print self.movie_name, "not found"
            else:            
                if not self.file_exists(self.fn_xml):
                    if not self.generate_xml():
                        print "ERROR: Couldn't create file: %s" % self.fn_xml
                        sys.exit(1)
                if not self.file_exists(self.fn_image):
                    if not self.generate_image():
                        print "ERROR: Couldn't create file: %s" % self.fn_image
                        sys.exit(2)            

if __name__ == '__main__':
    usage = "usage: %prog [options] URL"
    version = __version__
    parser = OptionParser(usage=usage, version="%prog "+version)

    parser.add_option("-r", "--rename-files", action='store_true', dest="rename", 
            default=True, help="Rename media files to match titles from TMDB")
    (options, args) = parser.parse_args()    

    basepath = os.getcwd()
    v = GenerateXML(basepath, options)
