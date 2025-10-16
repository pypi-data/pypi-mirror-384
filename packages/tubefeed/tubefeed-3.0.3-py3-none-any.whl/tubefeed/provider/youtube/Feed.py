import re
from datetime import datetime
from typing import Callable

from aiohttp import web

from .database import Channel, Playlist, Video
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
            channel.title,
            channel.description,
            channel.url,
            channel.title,
            self._url_builder(self._request, f'/channel/{channel.id}'),
            channel.title
        )

        channel_avatars = await channel.avatars()
        if len(channel_avatars) > 0:
            feed_channel.set_image(
                self._url_builder(self._request, f'/channel/{channel.id}/avatar.jpg'),
                channel.title,
                channel.url
            )

    async def load_playlist(self, playlist: Playlist, channel: Channel):
        feed_channel = self.set_channel(
            playlist.title,
            playlist.description,
            playlist.url,
            channel.title,
            self._url_builder(self._request, f'/playlist/{playlist.id}'),
            channel.title
        )

        playlist_thumbnails = await playlist.thumbnails()
        if len(playlist_thumbnails) > 0:
            feed_channel.set_image(
                self._url_builder(self._request, f'/playlist/{playlist.id}/thumbnail.jpg'),
                playlist.title,
                playlist.url
            )

    async def load_videos(self, videos: list[tuple[int, Video]]):
        for position, video in videos:
            # skip if video should be delayed further
            if video.published > self._datetime_threshold:
                continue

            feed_channel_item = self.channel.add_item(
                video.title,
                re.sub(r'\r?\n', '<br>', video.description),
                video.url,
                video.published,
                position,
                video.duration,
                self._url_builder(self._request, f'/video/{video.id}/audio.{self._ext}')
            )

            # feed_channel_item.set_image(
            #     self._url_builder(self._request, f'/video/{video.id}/thumbnail.jpg'),
            # )
