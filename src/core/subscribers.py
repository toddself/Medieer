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

from pubsub import pub
from core.filetools import rewind, process_file, generate_xml

def init():
    pub.subscribe(rewind, 'REWIND')
    pub.subscribe(process_file, 'PROCESS_FILE')
    pub.subscribe(genereate_xml, 'GENERATE_XML')

def main():
    init()

if __name__ == '__main__':
    main()