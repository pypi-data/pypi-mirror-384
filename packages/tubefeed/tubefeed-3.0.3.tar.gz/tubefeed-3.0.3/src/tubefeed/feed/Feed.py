import xml.etree.ElementTree as ET

from .FeedChannel import FeedChannel


class Feed:
    def __init__(self):
        self.channel: FeedChannel | None = None

    def to_xml(self) -> ET.Element:
        root = ET.Element('rss', version='2.0', **{
            'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        })

        if self.channel is not None:
            self.channel.to_xml(root)

        return root

    def __str__(self) -> str:
        return ET.tostring(self.to_xml(), encoding='utf-8').decode('utf-8')

    def set_channel(
            self, title: str, description: str, link: str, copyright: str, new_feed_url: str, author: str
    ) -> FeedChannel:
        self.channel = FeedChannel(title, description, link, copyright, new_feed_url, author)
        return self.channel
