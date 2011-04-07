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

import sys
import glob
from os.path import join as fjoin

from core.models import get_setting

VIDEO_EXTENSIONS = ['mov', 'mp4', 'm4v', 'wmv']

def reexec_with_pythonw(py_file=None):
    # Copyright (C) 2009 www.stani.be
    # Borrowed from the source to phatch!
    """'pythonw' needs to be called for any wxPython app
    to run from the command line on Mac Os X if python version < 2.5."""

    if sys.version.split(' ')[0] < '2.5' and sys.platform == 'darwin' and\
           not (sys.executable.endswith('/Python') or hasattr(sys, 'frozen')):
        sys.stderr.write('re-executing using pythonw')
        if not py_file:
            py_file = sys.argv[0]
        os.execvp('pythonw', ['pythonw', py_file] + sys.argv[1:])
        
def get_files():
    source_path = get_setting('source_path')
    file_list = []
    for ext in VIDEO_EXTENSIONS:
        file_list += glob.glob(fjoin(source_path, '*.%s' % ext))
    return file_list