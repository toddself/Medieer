#!/usr/bin/env python
from appdirs import AppDirs
from sqlobject.declarative import DeclarativeMeta

import io, data, gen, api

__APP_NAME__ = 'MediaInfo'
__APP_AUTHOR__ = 'Todd'
__VERSION__ = '0.10'

class MediaInfo():
    db_fn = '%s.sqlite' % __APP_NAME__
    dirs = AppDirs(__APP_NAME__, __APP_AUTHOR__, version=__VERSION__)
    
    def __init__(self, args):
        usage = "usage: %prog [options] URL"
        version = __VERSION__
        parser = OptionParser(usage=usage, version="%prog "+version)

        parser.add_option('-r', '--rename-files', action='store_false', dest='rename', 
                default=True, help='Rename media files to match titles')
        parser.add_option('-n', '--no-gui', action='store_false', dest='nogui', 
                default=True, help="Don't launch GUI; perform XML update via console")
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

    def process_files(self):
        self.t = api.TMDB()
        filelist = io.make_list(io.get_basepath())
        
        for videofile in filelist:
            (path, video_name, ext) = io.fn_to_parts(videofile)
            try:
                video = Media.select(Media.q.title==video_name)
    

        for fn_video in self.videos:
            self.tmdb = TMDB()
            if self.tmdb.genreCount() == 0:
                self.tmdb.populateGenres()

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
    mi = MediaInfo(argv[1:])