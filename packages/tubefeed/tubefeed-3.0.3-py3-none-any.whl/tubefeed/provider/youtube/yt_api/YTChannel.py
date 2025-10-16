from . import YouTube
from .YTPlaylist import YTPlaylist
from .YTThumbnail import YTThumbnail


class YTChannel:
    def __init__(self, yt: YouTube, item: dict):
        self._yt: YouTube = yt

        self.id: str = item['id']
        self.title: str = item['snippet']['title']
        self.description: str = item['snippet']['description']
        self.custom_url: str = item['snippet']['customUrl']
        self.thumbnails: list[YTThumbnail] = [YTThumbnail(n, t) for n, t in item['snippet']['thumbnails'].items()]

    async def uploads(self) -> YTPlaylist:
        result = await self._yt.get('channels', part='contentDetails', id=self.id)
        for item in result['items']:
            return await self._yt.get_playlist(item['contentDetails']['relatedPlaylists']['uploads'])
