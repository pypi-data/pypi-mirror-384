import xml.etree.ElementTree as ET


class FeedChannelImage:
    def __init__(self, url: str, title: str, link: str):
        self.url: str = url
        self.title: str = title
        self.link: str = link

    def to_xml(self, channel: ET.Element):
        image = ET.SubElement(channel, 'image')

        ET.SubElement(image, 'url').text = self.url
        ET.SubElement(image, 'title').text = self.title
        ET.SubElement(image, 'link').text = self.link
