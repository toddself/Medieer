#!/bin/bash
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

TEMP_DIR='/tmp/m_testdata'
MEDIA_DIRS=$(echo 'TV;Movies' | tr ";" "\n")

if [ -e $TEMP_DIR ]
then
    rm -rf $TEMP_DIR
fi

for dir in $MEDIA_DIRS
do
    mkdir -p $TEMP_DIR/$dir
done

touch $TEMP_DIR/Movies/Aliens.mp4
touch $TEMP_DIR/Movies/Empire\ Strikes\ Back.mp4
touch $TEMP_DIR/TV/Community\ S01E22.mp4
touch $TEMP_DIR/TV/The\ Simpsons\ S22E05.mp4
