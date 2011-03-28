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
from os.path import join as fjoin
from urllib2 import urlopen

from sqlobject import SQLObjectNotFound

from data import Settings

def make_list(basepath):
    allowed_extensions = ['m4v', 'mp4', 'mov', 'wmv']
    videos = []
    for root, dirs, files in os.walk(basepath):
        for name in files:
            if name.split('.')[-1] in allowed_extensions:
                videos.append(fjoin(root,name))
                
    return videos

def download_file(URL, dest):
    if "http" not in URL[:4]:
        raise ValueError('%s is not valid URLs must start with http')
        return False
    try:
        with open(dest, 'wb') as f:
            f.write(urlopen(URL).read())
            return True
    except OSError:
        return False

def generate_filename(movie_path, movie_name, extn):
    return fjoin(movie_path, "%s.%s" % (movie_name, extn))  
        
def fn_to_parts(fn):
    (path, full_filename) = fn.rsplit('/', 1)
    (base_filename, file_ext) = full_filename.rsplit('.', 1)
    return (path, base_filename, file_ext)
    
def get_basepath(default_path):
    try:
        os.stat(default_path)
        basepath = default_path
    except SQLObjectNotFound:
        basepath = os.getcwd()
    
    return basepath