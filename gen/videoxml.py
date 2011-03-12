#!/usr/bin/env python
import xmlwitch

class VideoXML():
    def __init__(self, media_library):
        self.medium = media_library
        self.makeXML()
    
    def makeXML(self):
        self.xml = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with self.xml.xml:
            with self.xml.viddb:
                for media in self.medium:
                    self.xml.origtitle(media.title)
                    self.xml.year(str(media.released.year))
                    self.xml.genre(','.join(media.listGenres()))
                    self.xml.mpaa("Rated %s" % media.rating)
                    self.xml.director(media.director.name)
                    self.xml.actors('     '.join(media.listActors()[:3]))
                    self.xml.description(media.description.decode('utf-8'))
                    self.xml.path(media.file_URI)
                    self.xml.length(str(media.runtime))
                    self.xml.videocodec(media.codec)
                    self.xml.poster(media.poster_local_URI)
