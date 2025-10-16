import xml.etree.ElementTree as ET


class FeedChannelItemImage:
    def __init__(self, url: str):
        self.url: str = url

    def to_xml(self, item: ET.Element):
        ET.SubElement(item, 'itunes:image', href=self.url)
