import xml.etree.ElementTree as ET
from datetime import datetime

from .FeedChannelItemImage import FeedChannelItemImage


class FeedChannelItem:
    def __init__(
            self,
            title: str, description: str, link: str, published: datetime, position: int, duration: int, audio_url: str
    ):
        self.title: str = title
        self.description: str = description
        self.link: str = link
        self.published: datetime = published
        self.position: int = position
        self.duration: int = duration
        self.audio_url: str = audio_url

        self.image: FeedChannelItemImage | None = None

    def to_xml(self, channel):
        item = ET.SubElement(channel, 'item')

        # general information
        ET.SubElement(item, 'title').text = self.title
        ET.SubElement(item, 'description').text = self.description
        ET.SubElement(item, 'link').text = self.link
        ET.SubElement(item, 'pubDate').text = self.published.strftime('%a, %d %b %Y %H:%M:%S GMT')

        ET.SubElement(item, 'enclosure', url=self.audio_url)

        ET.SubElement(item, 'itunes:title').text = self.title
        ET.SubElement(item, 'itunes:summary').text = self.description
        ET.SubElement(item, 'itunes:episodeType').text = 'full'
        ET.SubElement(item, 'itunes:episode').text = str(self.position)

        # see https://help.apple.com/itc/podcasts_connect/#/itcb54353390
        ET.SubElement(item, 'itunes:duration').text = str(self.duration)

        # image
        if self.image is not None:
            self.image.to_xml(item)

    def set_image(self, url: str) -> FeedChannelItemImage:
        self.image = FeedChannelItemImage(url)
        return self.image
