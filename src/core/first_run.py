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
from core.models import Settings

def first_run(appdir):
    # make user data directory
    if not os.path.isdir(appdir):
        try:
            os.makedirs(appdir)
        except OSError:
            sys.exit('Unable to create directory: %s.' % appdir)
            
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
      s = Settings(key='organization_method', value='directory') 
    else:
      s = Settings(key='organization_method', value='videoxml')

    # key: master_org
    # options: true or false
    # this dictates whether or not Medieer.organize_files() is called
    if master_org == 'y':
      s = Settings(key='master_org', value='true')
    else:
      s = Settings(key='master_org', value='false')

    # key: movies_by_genre
    # options: true or false
    # this dictates whether or not movies are located in subdirectories
    # according to genre.  uses the first genre in the list, which
    # we consider to be the 'main' genre
    if movie_genre == 'y':
      s = Settings(key='movies_by_genre', value='true')
    else:
      s = Settings(key='movies_by_genre', value='false')

    # key: tv_series_by_genre
    # options: true or false
    if tv_series_genre == 'y':
      s = Settings(key='tv_series_by_genre', value='true')
    else:
      s = Settings(key='tv_series_by_genre', value='false')

    # key: tv_series_org
    # options: true or false
    if tv_series_org == 'y':
      s = Settings(key='tv_series_by_series', value='true')
    else:
      s = Settings(key='tv_series_by_series', value='false')

    # key: dest_path
    # options: any valid directory
    # this option determines where the system will check for video files
    # as a default, and to where the additional generated files will be
    # stored.            
    s = Settings(key='dest_path', value=dest_path)

    # key: basepath
    # options: any valid directory
    # this option dictates where input files will be found.
    # defaults to the dest_path
    s = Settings(key='source_path', value=source_path)

