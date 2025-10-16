import logging
import os
from datetime import datetime, timedelta
from typing import Iterator
from uuid import uuid4

from aiohttp import web

from .Feed import Feed
from .database import Database, Channel
from .twitch_api import Twitch, TwChannel
from .. import HANDLER_TYPE
from ...database import BaseDB
from ...media import Downloader
from ...provider import Provider


class TwitchProvider(Provider):
    PROVIDER_NAME = 'twitch'

    def __init__(self):
        self._logger = logging.getLogger(self.PROVIDER_NAME)

        # Twitch credentials
        if 'TWITCH_CLIENT_ID' not in os.environ or 'TWITCH_CLIENT_SECRET' not in os.environ:
            self._disabled: bool = True
            self._logger.warning('TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET is not set (Twitch integration is disabled)')
            return
        else:
            self._disabled: bool = False

        self._client_id: str = os.environ.get('TWITCH_CLIENT_ID')
        self._client_secret: str = os.environ.get('TWITCH_CLIENT_SECRET')
        self._logger.warning('CLIENT_ID and CLIENT_SECRET is set')

        # download options
        self._default_feed_format = os.environ.get('TWITCH_DEFAULT_FEED_FORMAT', 'webm')
        self._logger.warning(f'default feed format is {self._default_feed_format}')

        self._download_format = os.environ.get('TWITCH_DOWNLOAD_FORMAT', 'Audio_Only')
        self._logger.warning(f'format for download is {self._download_format}')

        # max download rate
        self._max_download_rate: str = os.environ.get('TWITCH_MAX_DOWNLOAD_RATE', None)
        self._logger.warning(f'max download rate is {self._max_download_rate}')

        # re-encode options
        self._reencode_aac_bitrate = os.environ.get('TWITCH_REENCODE_AAC_BITRATE', None)
        if self._reencode_aac_bitrate is None:
            self._logger.warning('re-encode for aac disabled')
        else:
            self._logger.warning(f're-encode bitrate for aac is {self._reencode_aac_bitrate}')

        self._reencode_opus_bitrate = os.environ.get('TWITCH_REENCODE_OPUS_BITRATE', '128k')
        self._logger.warning(f're-encode bitrate for opus is {self._reencode_opus_bitrate}')

    @property
    def database_class(self) -> type[BaseDB]:
        return Database

    @property
    def routes(self) -> Iterator[tuple[list[str], str, HANDLER_TYPE]]:
        if self._disabled:
            return

        yield (['/name/{name}.{ext}', '/name/{name}'],
               'receive a channel feed by name',
               self.get_channel_by_name)
        yield (['/channel/{id}.{ext}', '/channel/{id}'],
               'receive a channel feed by id',
               self.get_channel_by_id)
        yield (['/channel/{id}/avatar.jpg'],
               'download a channel avatar',
               self.get_channel_avatar)
        yield (['/video/{id}/audio.{ext}'],
               'download a video audio',
               self.get_video_audio)

    async def get_channel_by_name(self, request: web.Request):
        name: str = request.match_info.get('name')
        name = name.lower()

        async with (
            Database(request.app['database_path']) as db,
            Twitch(self._client_id, self._client_secret) as twitch
        ):
            tw_channel = await twitch.get_channel_by_name(name)
            db_channel = await db.add_channel(tw_channel, datetime.now())

            return await self._build_channel_feed(request, db_channel, tw_channel)

    async def get_channel_by_id(self, request: web.Request):
        id: str = request.match_info.get('id')

        async with (
            Database(request.app['database_path']) as db,
            Twitch(self._client_id, self._client_secret) as twitch
        ):
            tw_channel = await twitch.get_channel_by_id(id)
            db_channel = await db.add_channel(tw_channel, datetime.now())

            return await self._build_channel_feed(request, db_channel, tw_channel)

    async def _build_channel_feed(self,
                                  request: web.Request,
                                  db_channel: Channel, twitch_channel: TwChannel) -> web.Response:
        # get requested extension
        ext: str = request.match_info.get('ext') or self._default_feed_format
        delay: int = int(request.query.get('delay', '0'))

        if ext not in ('m4a', 'webm'):
            return web.HTTPNotFound()

        datetime_threshold = datetime.now() - timedelta(seconds=delay)

        # get and sort videos
        twitch_videos = list(reversed(list(enumerate(reversed(await twitch_channel.get_videos()), start=1))))

        # store videos in database
        for _, video in twitch_videos:
            await db_channel.add_video(video)

        # build feed
        feed = Feed(request, self.url, ext, datetime_threshold)
        await feed.load_channel(twitch_channel)
        await feed.load_videos(twitch_videos)

        # convert feed to text
        return web.Response(text=str(feed), content_type='application/xml')

    async def get_channel_avatar(self, request: web.Request):
        id: str = request.match_info.get('id')

        async with Database(request.app['database_path']) as db:
            channel = await db.get_channel_by_id(id)
            return web.HTTPFound(channel.profile_image_url)

    async def get_video_audio(self, request: web.Request):
        now = datetime.now()

        id: str = request.match_info.get('id')
        ext: str = request.match_info.get('ext')

        if ext == 'm4a':
            ffmpeg_bitrate: str | None = self._reencode_aac_bitrate
            ffmpeg_format: str = 'aac' if ffmpeg_bitrate is not None else None
            mime_type = 'audio/m4a'
        elif ext == 'webm':
            ffmpeg_bitrate: str = self._reencode_opus_bitrate
            ffmpeg_format: str = 'libopus'
            mime_type = 'audio/webm'
        else:
            raise web.HTTPNotFound()

        # receive video from database
        async with Database(request.app['database_path']) as db:
            video = await db.get_video(id)
            if video is None:
                raise web.HTTPNotFound(reason=f'video {id} not found')

            outdated_files = await db.outdated_files(now - timedelta(hours=12))
            for file in outdated_files:
                self._logger.info(f'delete outdated file {file.path} for video {file.video_id}')
                await file.delete()

            video_file = await video.get_file(ext)

        # download file only if not already stored
        if video_file is not None:
            self._logger.info(f'serve {id} from cached file')

        else:
            self._logger.info(f'need to download {id}')

            # download audio
            output_path = request.app['download_dir'] / f'{str(uuid4())}.{ext}'

            audio_downloader = Downloader(video.url, self._download_format, ffmpeg_format, ffmpeg_bitrate)
            await audio_downloader.download_to(output_path, self._max_download_rate, logger=self._logger)

            # store file path in database
            async with Database(request.app['database_path']) as db:
                video._db = db
                video_file = await video.set_file(output_path, ext)

        # send file
        return web.FileResponse(video_file.path, headers={
            'Content-Type': mime_type
        })
