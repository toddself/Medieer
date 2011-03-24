#!/bin/bash
TEMP_DIR='/tmp/media_info_testdata'
MEDIA_DIRS=$(echo 'tv;movies' | tr ";" "\n")

if [ -e $TEMP_DIR ]
then
    rm -rf $TEMP_DIR
fi

for dir in $MEDIA_DIRS
do
    mkdir -p $TEMP_DIR/$dir
done

touch $TEMP_DIR/movies/Aliens.mp4
touch $TEMP_DIR/movies/Empire\ Strikes\ Back.mp4
touch $TEMP_DIR/tv/Community\ S01E22.mp4
touch $TEMP_DIR/tv/The\ Simpsons\ S22E05.mp4
