import xml.etree.ElementTree as ET
from datetime import datetime

from .FeedChannelImage import FeedChannelImage
from .FeedChannelItem import FeedChannelItem


class FeedChannel:
    def __init__(self, title: str, description: str, link: str, copyright: str, new_feed_url: str, author: str):
        self.title: str = title
        self.description: str = description
        self.link: str = link
        self.copyright: str = copyright
        self.new_feed_url: str = new_feed_url
        self.author: str = author

        self.image: FeedChannelImage | None = None

        self.items: list[FeedChannelItem] = []

    def to_xml(self, root: ET.Element):
        channel = ET.SubElement(root, 'channel')

        # general information
        ET.SubElement(channel, 'title').text = self.title
        ET.SubElement(channel, 'description').text = self.description
        ET.SubElement(channel, 'link').text = self.link
        ET.SubElement(channel, 'copyright').text = self.copyright

        ET.SubElement(channel, 'itunes:summary').text = self.description
        ET.SubElement(channel, 'itunes:type').text = 'episodic'
        ET.SubElement(channel, 'itunes:new-feed-url').text = self.new_feed_url
        ET.SubElement(channel, 'itunes:author').text = self.author

        # image
        if self.image is not None:
            self.image.to_xml(channel)
            ET.SubElement(channel, 'itunes:image', href=self.image.url)

        # items
        for item in self.items:
            item.to_xml(channel)

    def set_image(self, url: str, title: str, link: str) -> FeedChannelImage:
        self.image = FeedChannelImage(url, title, link)
        return self.image

    def add_item(
            self,
            title: str, description: str, link: str, published: datetime, position: int, duration: int, audio_url: str
    ) -> FeedChannelItem:
        new_item = FeedChannelItem(title, description, link, published, position, duration, audio_url)

        self.items.append(new_item)
        return new_item
