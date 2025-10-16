from datetime import datetime
from typing import Callable

from aiohttp import web

from .twitch_api import TwChannel as Channel, TwVideo as Video
from ...feed import Feed as BaseFeed


class Feed(BaseFeed):
    def __init__(self,
                 request: web.Request,
                 url_builder: Callable[[web.Request, str], str],
                 ext: str,
                 datetime_threshold: datetime):
        super().__init__()

        self._request: web.Request = request
        self._url_builder: Callable[[web.Request, str], str] = url_builder
        self._ext: str = ext
        self._datetime_threshold: datetime = datetime_threshold

    async def load_channel(self, channel: Channel):
        feed_channel = self.set_channel(
            channel.display_name,
            channel.description,
            channel.url,
            channel.display_name,
            self._url_builder(self._request, f'/channel/{channel.id}'),
            channel.display_name
        )

        feed_channel.set_image(
            self._url_builder(self._request, f'/channel/{channel.id}/avatar.jpg'),
            channel.display_name,
            channel.url
        )

    async def load_videos(self, videos: list[tuple[int, Video]]):
        for position, video in videos:
            self.channel.add_item(
                video.title,
                video.description,
                video.url,
                video.published_at,
                position,
                video.duration,
                self._url_builder(self._request, f'/video/{video.id}/audio.{self._ext}')
            )
