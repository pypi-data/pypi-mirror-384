import asyncio
import logging
import os
from datetime import datetime, timedelta
from functools import reduce
from typing import Iterator
from uuid import uuid4

from aiohttp import web
from aiohttp.web_fileresponse import FileResponse

from .ChapterList import ChapterList
from .Feed import Feed
from .database import Database, Channel, Playlist
from .sb_api import SponsorBlock
from .yt_api import YouTube, YTError, YTPlaylist
from .. import HANDLER_TYPE, Provider
from ...media import Downloader


class YouTubeProvider(Provider):
    PROVIDER_NAME = 'youtube'

    def __init__(self):
        self._logger = logging.getLogger(self.PROVIDER_NAME)

        # YouTube API key
        if 'YT_API_KEY' not in os.environ:
            self._disabled: bool = True
            self._logger.error('YT_API_KEY is not set (YouTube integration is disabled)')
            return
        else:
            self._disabled: bool = False

        self._api_key: str = os.environ.get('YT_API_KEY')
        self._logger.warning('API key is set')

        # feed settings
        self._delay_static = int(os.environ.get('YT_DELAY_STATIC', '600'))
        self._logger.warning(f'static delay set to {self._delay_static}s')

        self._delay_factor = int(os.environ.get('YT_DELAY_DURATION_FACTOR', '1'))
        self._logger.warning(f'delay duration factor set to {self._delay_factor}x')

        self._feed_limit: int | None = int(os.environ.get('YT_FEED_LIMIT', '0')) or None
        if self._feed_limit is not None:
            self._logger.warning(f'feed size is limited to {self._feed_limit}')

        # download options
        self._default_feed_format = os.environ.get('YT_DEFAULT_FEED_FORMAT', 'webm')
        self._logger.warning(f'default feed format is {self._default_feed_format}')

        self._aac_download_format = os.environ.get('YT_AAC_DOWNLOAD_FORMAT', 'bestaudio[ext=m4a]')
        self._logger.warning(f'format for aac downloads is {self._aac_download_format}')

        self._opus_download_format = os.environ.get('YT_OPUS_DOWNLOAD_FORMAT', 'bestaudio[ext=webm]')
        self._logger.warning(f'format for opus downloads is {self._opus_download_format}')

        # max download rate
        self._max_download_rate: str = os.environ.get('YT_MAX_DOWNLOAD_RATE', None)
        self._logger.warning(f'max download rate is {self._max_download_rate}')

        # re-encode options
        self._reencode_aac_bitrate = os.environ.get('YT_REENCODE_AAC_BITRATE', None)
        if self._reencode_aac_bitrate is None:
            self._logger.warning('re-encode for aac disabled')
        else:
            self._logger.warning(f're-encode bitrate for aac is {self._reencode_aac_bitrate}')

        self._reencode_opus_bitrate = os.environ.get('YT_REENCODE_OPUS_BITRATE', None)
        if self._reencode_opus_bitrate is None:
            self._logger.warning('re-encode for opus disabled')
        else:
            self._logger.warning(f're-encode bitrate for opus is {self._reencode_opus_bitrate}')

        # sponsorblock
        self._sponsorblock: bool = os.environ.get('YT_SPONSORBLOCK', '').lower() in ('true', 'yes', '1')
        if self._sponsorblock:
            self._logger.warning('sponsorblock is enabled')
        else:
            self._logger.warning('sponsorblock is disabled')

    @property
    def database_class(self) -> type[Database]:
        return Database

    @property
    def routes(self) -> Iterator[tuple[list[str], str, HANDLER_TYPE]]:
        if self._disabled:
            return

        yield (['/handle/{handle}.{ext}', '/handle/{handle}'],
               'receive a channel feed by handle',
               self.get_channel_by_handle)
        yield (['/handle/{handle}/avatar.jpg'],
               'get a channel avatar by handle',
               self.get_channel_avatar_by_handle)
        yield (['/channel/{id}.{ext}', '/channel/{id}'],
               'receive a channel feed by id',
               self.get_channel_by_id)
        yield (['/channel/{id}/avatar.jpg'],
               'get a channel avatar by id',
               self.get_channel_avatar_by_id)
        yield (['/playlist/{id}.{ext}', '/playlist/{id}'],
               'receive a playlist',
               self.get_playlist)
        yield (['/playlist/{id}/thumbnail.jpg'],
               'get a playlist thumbnail',
               self.get_playlist_thumbnail)
        yield (['/video/{id}/thumbnail.jpg'],
               'get a video thumbnail',
               self.get_video_thumbnail)
        yield (['/video/{id}/audio.{ext}'],
               'download a video audio',
               self.get_video_audio)

    async def get_channel_by_handle(self, request: web.Request):
        handle: str = request.match_info.get('handle').lower()
        ext: str | None = request.match_info.get('ext')

        if not handle.startswith('@'):
            handle = f'@{handle}'

        # ensure channel is in database
        async with Database(request.app['database_path']) as db:
            channel = await self.ensure_channel_handle_in_db(db, handle)

        # return response
        return await self.get_channel_by_id(request, channel.id, ext)

    async def get_channel_avatar_by_handle(self, request: web.Request):
        handle: str = request.match_info.get('handle')
        handle = handle.lower()

        # ensure channel is in database
        async with Database(request.app['database_path']) as db:
            channel = await self.ensure_channel_handle_in_db(db, handle)

        # return response
        return await self.get_channel_avatar_by_id(request, channel.id)

    async def get_channel_by_id(self, request: web.Request, id: str = None, ext: str = None):
        id: str = id or request.match_info.get('id')
        ext: str | None = ext or request.match_info.get('ext') or self._default_feed_format
        include: list[str] = request.query.get('include', 'videos livestreams').split(' ')
        delay: int = int(request.query.get('delay', '0'))

        if ext not in ('m4a', 'webm'):
            return web.HTTPNotFound()

        datetime_threshold = datetime.now() - timedelta(seconds=delay)

        # ensure channel is in database and build feed
        async with (Database(request.app['database_path']) as db):
            # load channel from database
            channel = await self.ensure_channel_id_in_db(db, id)

            # run get_playlist to update playlist items
            channel_uploads = await channel.uploads()
            channel_playlists = [
                c
                for c in await channel_uploads.children()
                if c.child_name in include
            ]

            await asyncio.gather(*(
                self.ensure_playlist_in_db(db, c)
                for c in channel_playlists
            ))

            # get videos from all playlists
            union = reduce(lambda a, v: a | v, channel_playlists)
            videos = [(p, v) async for p, _, v in union.videos(self._feed_limit)]

            # build feed
            feed = Feed(request, self.url, ext, datetime_threshold)
            await feed.load_channel(channel)
            await feed.load_videos(videos)

        # return response
        return web.Response(text=str(feed), content_type='application/xml')

    async def get_channel_avatar_by_id(self, request: web.Request, id: str = None):
        id: str = id or request.match_info.get('id')

        # get channel and avatars from database
        async with Database(request.app['database_path']) as db:
            channel = await self.ensure_channel_id_in_db(db, id)
            avatars = await channel.avatars()

        # return error if no avatar is found
        if len(avatars) == 0:
            raise web.HTTPNotFound(reason=f'no avatar found for channel {id=}')

        # select avatar with max size
        avatar_url = max(avatars, key=lambda a: a.width).url

        # send redirect to client
        return web.HTTPFound(location=avatar_url)

    async def get_playlist(self, request: web.Request):
        id: str = request.match_info.get('id')
        ext: str = request.match_info.get('ext') or self._default_feed_format
        delay: int = int(request.query.get('delay', '0'))

        if ext not in ('m4a', 'webm'):
            return web.HTTPNotFound()

        datetime_threshold = datetime.now() - timedelta(seconds=delay)

        # ensure playlist is in database and build feed
        async with Database(request.app['database_path']) as db:
            # get data from database
            playlist = await self.ensure_playlist_in_db(db, id)
            channel = await playlist.channel()
            videos = [(p, v) async for p, _, v in playlist.videos(self._feed_limit)]

            # build feed
            feed = Feed(request, self.url, ext, datetime_threshold)
            await feed.load_playlist(playlist, channel)
            await feed.load_videos(videos)

        # return response
        return web.Response(text=str(feed), content_type='application/xml')

    async def get_playlist_thumbnail(self, request: web.Request):
        id: str = request.match_info.get('id')

        # get playlist and thumbnails from database
        async with Database(request.app['database_path']) as db:
            playlist = await self.ensure_playlist_in_db(db, id)
            thumbnails = await playlist.thumbnails()

        # return error if no thumbnail is found
        if len(thumbnails) == 0:
            raise web.HTTPNotFound(reason=f'no thumbnail found for {id}')

        # select thumbnail with max size
        thumbnail_url = max(thumbnails, key=lambda a: a.width).url

        # send redirect to client
        return web.HTTPFound(location=thumbnail_url)

    async def get_video_thumbnail(self, request: web.Request):
        id: str = request.match_info.get('id')

        # get video and thumbnails from database
        async with Database(request.app['database_path']) as db:
            video = await db.get_video(id)
            if video is None:
                raise web.HTTPNotFound(reason=f'video {id} not found')

            thumbnails = await video.thumbnails()

        # return error if no thumbnail is found
        if len(thumbnails) == 0:
            raise web.HTTPNotFound(reason=f'no thumbnail found for {id}')

        # select thumbnail with max size
        thumbnail_url = max(thumbnails, key=lambda a: a.width).url

        # send redirect to client
        return web.HTTPFound(location=thumbnail_url)

    async def get_video_audio(self, request: web.Request):
        now = datetime.now()

        id: str = request.match_info.get('id')
        ext: str = request.match_info.get('ext')

        if ext == 'm4a':
            yt_format: str | None = self._aac_download_format
            ffmpeg_bitrate: str | None = self._reencode_aac_bitrate
            ffmpeg_format: str = 'aac' if ffmpeg_bitrate is not None else None
            mime_type = 'audio/m4a'
        elif ext == 'webm':
            yt_format: str | None = self._opus_download_format
            ffmpeg_bitrate: str | None = self._reencode_opus_bitrate
            ffmpeg_format: str = 'libopus' if ffmpeg_bitrate is not None else None
            mime_type = 'audio/webm'
        else:
            raise web.HTTPNotFound()

        # receive video info from database
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

            # extract chapters
            video_chapters = ChapterList.from_video(video.title, video.duration)
            description_chapters = ChapterList.from_description(video.description, video.duration)

            if self._sponsorblock:
                async with SponsorBlock() as sb:
                    sb_chapters = await ChapterList.from_sponsorblock(await sb.skip_segments(video.id))
            else:
                sb_chapters = ChapterList([])

            all_chapters = video_chapters & description_chapters & sb_chapters

            # download audio
            output_path = request.app['download_dir'] / f'{str(uuid4())}.{ext}'

            audio_downloader = Downloader(video.url, yt_format, ffmpeg_format, ffmpeg_bitrate)
            await audio_downloader.download_to(output_path, self._max_download_rate, all_chapters, self._logger)

            # store file path in database
            async with Database(request.app['database_path']) as db:
                video._db = db
                video_file = await video.set_file(output_path, ext)

        # send file
        return FileResponse(video_file.path, headers={
            'Content-Type': mime_type
        })

    async def ensure_channel_in_db(self, db: Database, now: datetime, id: str = None, handle: str = None) -> Channel:
        async with YouTube(self._api_key) as yt:
            try:
                # search for id / handle
                for yt_c in await yt.find_channels(id=id, handle=handle):
                    # get uploads playlist
                    yt_u = await yt_c.uploads()

                    # store in database
                    channel = await db.add_channel(yt_c, yt_u, now)

                    # break so no 404 is raised
                    break

                # handle not found
                else:
                    raise web.HTTPNotFound(reason=f'channel {id=} / {handle=} not found')

            # error from YouTube
            except YTError as e:
                error = web.HTTPException(reason=e.message)
                error.status_code = e.code

                raise error

        await db.commit()
        return channel

    async def ensure_channel_handle_in_db(self, db: Database, handle: str) -> Channel:
        now = datetime.now()

        # get channel object from database
        channel = await db.get_channel_by_handle(handle)

        # fetch from YouTube if missing in database
        if channel is None or channel.updated < now - timedelta(days=7):
            channel = await self.ensure_channel_in_db(db, now, handle=handle)

        return channel

    async def ensure_channel_id_in_db(self, db: Database, id: str) -> Channel:
        now = datetime.now()

        # get channel object from database
        channel = await db.get_channel_by_id(id)

        # fetch from YouTube if missing in database
        if channel is None or channel.updated < now - timedelta(days=7):
            channel = await self.ensure_channel_in_db(db, now, id=id)

        return channel

    async def ensure_playlist_in_db(self, db: Database, playlist: str | Playlist) -> Playlist:
        now = datetime.now()

        async with YouTube(self._api_key) as yt:
            # If the given playlist is a Playlist object from the database
            # package, we just need to create a yt_pl object to use later.
            if isinstance(playlist, Playlist):
                yt_pl = YTPlaylist.from_id(yt, playlist.id)

            # If the given playlist is a string / id, we need to get the
            # object from the database or create it with data from YouTube
            # before updating the videos.
            else:
                id = playlist

                # get playlist object from database
                playlist = await db.get_playlist(id)

                if playlist is not None:
                    yt_pl = YTPlaylist.from_id(yt, id)

                # fetch playlist from YouTube if missing in database
                else:
                    try:
                        # fetch playlist
                        yt_pl = await yt.get_playlist(id)
                        if yt_pl is None:
                            raise web.HTTPNotFound(reason=f'playlist {id} not found')

                        # check if channel is not already in database
                        channel = await db.get_channel_by_id(yt_pl.channel_id)

                        if channel is None or channel.updated < now - timedelta(days=7):
                            # fetch channel and store in database
                            yt_ch = await yt_pl.channel()
                            yt_ch_u = await yt_ch.uploads()

                            channel = await db.add_channel(yt_ch, yt_ch_u, now)

                        # store playlist in database
                        playlist = await channel.add_playlist(yt_pl)

                    # error from YouTube
                    except YTError as e:
                        error = web.HTTPException(reason=e.message)
                        error.status_code = e.code

                        raise error

            # We request the playlist items from YouTube and store the missing
            # ones in the database.
            try:
                async for yt_videos in yt_pl.videos():
                    # fetch video objects from database
                    db_videos = await asyncio.gather(*(playlist.get_video(v.id) for v in yt_videos))

                    # find missing videos
                    yt_v_missing = [yt_v for db_v, yt_v in zip(db_videos, yt_videos) if db_v is None]

                    # receive details for missing videos
                    yt_v_details = await yt.get_videos(yt_v_missing)

                    # store in database
                    yt_v_insert = (
                        (v, int(v.published.timestamp()) + max(self._delay_static, v.duration * self._delay_factor))
                        for v in yt_v_details
                    )

                    await asyncio.gather(*(
                        playlist.add_video(v, sk)
                        for v, sk in yt_v_insert
                        if not v.is_live and sk <= now.timestamp()
                    ))

                    # break if oldest fetched video is already in db
                    if db_videos[-1] is not None:
                        break

            except YTError as e:
                # Under some circumstances we do not want to raise an error here.
                # If a channel did not upload a single short for example, the
                # playlist does not exist. This is expected behaviour though.
                if not playlist.child_name or e.code != 404:
                    raise e

        await db.commit()
        return playlist
