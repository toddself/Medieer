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

import os

from pubsub import pub
from sqlobject import DeclarativeMeta

from core import models
from lib.tmdb import TMDB, import_genre_data
from console.console import ask, ask_yes_no

def create_tables():
    # make tables
    for cname in models._core_models:
      cl = eval('models.%s' % cname)
      if isinstance(cl, DeclarativeMeta):
          if not cl.tableExists():
              pub.sendMessage("LOGGER", 
                              module=__name__, 
                              level='DEBUG', 
                              msg="Creating table %s" % cname)
              cl.createTable()    

def make_data_dir(appdir):
    # make user data directory
    if not os.path.isdir(appdir):
        try:
            os.makedirs(appdir)
        except OSError:
            sys.exit('Unable to create directory: %s.' % appdir)

def ask_path(self, question, path):
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
                pub.sendMessage("LOGGER",
                                module=__name__,
                                level='DEBUG',
                                msg="Can't create: %s" % path)
                print "Error: can't create %s" % path   
        else:
            path_ready = True
    return path     

def main(appdir):
    make_data_dir(appdir)
    create_tables()
    import_genre_data()
    
    # set default settings
    org_method = ask('Catalog files by directory or XML Manifest? [XML/dir] ', 
                     ['xml','dir']) == 'xml'
    master_org = ask_yes_no('Organize your files? [YES/no] ')
    movie_genre = ask_yes_no('Organize movies by genre? [YES/no] ')
    tv_series_genre = ask_yes_no('Organize TV by genre? [yes/NO] ', 
                                 default='n')
    tv_series_org = ask_yes_no('Organize TV by series and season? [YES/no] ')
    source_path = ask_path('Where are your media files located? ', appdir)
    if master_org == 'y':
      dest_path = ask_path('Where should I place your organized files? ', 
                            appdir)
      
    s = Settings(key='organization_method', value=org_method) 
    s = Settings(key='master_org', value=master_org)
    s = Settings(key='movies_by_genre', value=movie_genre)
    s = Settings(key='tv_series_by_genre', value=tv_series_genre)
    s = Settings(key='tv_series_by_series', value=tv_series_org)
    s = Settings(key='dest_path', value=dest_path)
    s = Settings(key='source_path', value=source_path)