#!/usr/bin/env python
from lxml import etree

# TODO: SWITCH TO BEAUTIFULSOUP IF POSSIBLE

class VideoXML():
    def __init__(self):
        pass
        
    def toxml(self, pretty=False):
        return etree.tounicode(self.xml, pretty_print=pretty)
        
    def makeVideoXML(self, video):
        self.xml = etree.Element('video')
        
        title = etree.SubElement(self.xml, 'title')
        title.text = video.title

        year = etree.SubElement(self.xml, 'year')
        year.text = str(video.released.year)

        genre = etree.SubElement(self.xml, 'genre')
        genre.text = video.listGenres(prepend_media_type=False)[0]

        mpaa = etree.SubElement(self.xml, 'mpaa')
        mpaa.text = video.rating

        director = etree.SubElement(self.xml, 'director')
        director.text = video.director.name

        actors = etree.SubElement(self.xml, 'actors')
        actors.text = '     '.join(video.listActors()[:3])

        description = etree.SubElement(self.xml, 'description')
        description.text = video.description

        length = etree.SubElement(self.xml, 'length')
        length.text = str(video.runtime)
        
    
    def makeVideoDirectory(self, media):
        self.xml = etree.Element('xml')
        self.viddb = etree.SubElement(self.xml, 'viddb')
        for video in media:
            self.addVideo(video)
            
    def addVideo(self, video):
        movie = etree.SubElement(self.viddb, 'movie')
        
        origtitle = etree.SubElement(movie, 'origtitle')
        origtitle.text = video.title
        
        year = etree.SubElement(movie, 'year')
        year.text = str(video.released.year)
        
        genre = etree.SubElement(movie, 'genre')
        genre.text = ','.join(video.listGenres())
        
        mpaa = etree.SubElement(movie, 'mpaa')
        mpaa.text = 'Rated %s' % video.rating
        
        director = etree.SubElement(movie, 'director')
        director.text = video.director.name
        
        actors = etree.SubElement(movie, 'actors')
        actors.text = '     '.join(video.listActors()[:3])
        
        description = etree.SubElement(movie, 'description')
        description.text = video.description
        
        path = etree.SubElement(movie, 'path')
        path.text = video.file_URI
        
        length = etree.SubElement(movie, 'length')
        length.text = str(video.runtime)
        
        videocodec = etree.SubElement(movie, 'videocodec')
        videocodec.text = video.codec
        
        poster = etree.SubElement(movie, 'poster')
        poster.text = video.poster_local_URI

        return movie