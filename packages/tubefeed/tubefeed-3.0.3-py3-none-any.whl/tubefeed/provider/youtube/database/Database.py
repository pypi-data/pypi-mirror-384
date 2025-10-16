import asyncio
from datetime import datetime
from pathlib import Path

from .Channel import Channel
from .File import File
from .Playlist import Playlist
from .Video import Video
from ..yt_api import YTChannel, YTPlaylist
from ....database import BaseDB


class Database(BaseDB):
    async def create_tables(self):
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_channels (
                id          VARCHAR  PRIMARY KEY,
                title       VARCHAR  NOT NULL,
                description TEXT     NOT NULL,
                custom_url  VARCHAR  NOT NULL,
                uploads     VARCHAR  NOT NULL,
                updated     DATETIME NOT NULL,
                FOREIGN KEY (uploads) REFERENCES youtube_playlists(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
                    DEFERRABLE INITIALLY DEFERRED
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_handles (
                handle  VARCHAR PRIMARY KEY,
                channel VARCHAR NOT NULL,
                FOREIGN KEY (channel) REFERENCES youtube_channels(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_avatars (
                channel VARCHAR NOT NULL,
                name    VARCHAR NOT NULL,
                width   INTEGER NOT NULL,
                height  INTEGER NOT NULL,
                url     VARCHAR NOT NULL,
                PRIMARY KEY (channel, name),
                FOREIGN KEY (channel) REFERENCES youtube_channels(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_playlists (
                id          VARCHAR PRIMARY KEY,
                parent      VARCHAR,
                child_name  VARCHAR,
                channel     VARCHAR NOT NULL,
                title       VARCHAR NOT NULL,
                description VARCHAR NOT NULL,
                published   DATETIME NOT NULL,
                UNIQUE (parent, child_name),
                FOREIGN KEY (parent) REFERENCES youtube_playlists(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
                FOREIGN KEY (channel) REFERENCES youtube_channels(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_playlist_thumbnails (
                playlist VARCHAR NOT NULL,
                name     VARCHAR NOT NULL,
                width    INTEGER NOT NULL,
                height   INTEGER NOT NULL,
                url      VARCHAR NOT NULL,
                PRIMARY KEY (playlist, name),
                FOREIGN KEY (playlist) REFERENCES youtube_playlists(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_videos (
                id          VARCHAR  PRIMARY KEY,
                title       VARCHAR  NOT NULL,
                description TEXT     NOT NULL,
                published   DATETIME NOT NULL,
                duration    INTEGER  NOT NULL
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_video_thumbnails (
                video   VARCHAR NOT NULL,
                name    VARCHAR NOT NULL,
                width   INTEGER NOT NULL,
                height  INTEGER NOT NULL,
                url     VARCHAR NOT NULL,
                PRIMARY KEY (video, name),
                FOREIGN KEY (video) REFERENCES youtube_videos(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_in_playlist(
                playlist VARCHAR NOT NULL,
                video    VARCHAR NOT NULL,
                sort_key INTEGER NOT NULL,
                PRIMARY KEY (playlist, video),
                FOREIGN KEY (playlist) REFERENCES youtube_playlists(id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (video) REFERENCES youtube_videos(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS youtube_video_files (
                video     VARCHAR NOT NULL,
                extension VARCHAR NOT NULL,
                path      VARCHAR NOT NULL,
                added     DATETIME NOT NULL,
                PRIMARY KEY (video, extension),
                FOREIGN KEY (video) REFERENCES youtube_videos(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE INDEX IF NOT EXISTS idx_youtube_video_files_added
            ON youtube_video_files(added)
        ''')

    async def get_channel_by_id(self, id: str) -> Channel | None:
        async for row in await self.con.execute('''
            SELECT *
            FROM youtube_channels
            WHERE id = ?
        ''', (id,)):
            return Channel(self, *row)

    async def get_channel_by_handle(self, handle: str) -> Channel | None:
        async for row in await self.con.execute('''
            SELECT channels.*
            FROM youtube_channels channels
            JOIN youtube_handles handles
                ON channels.id = handles.channel
            WHERE handles.handle = ?
        ''', (handle,)):
            return Channel(self, *row)

    async def add_channel(self, channel: YTChannel, uploads: YTPlaylist, updated: datetime) -> Channel:
        await self.con.execute('''
            INSERT INTO youtube_channels
                VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (id)
                DO UPDATE SET
                    title = ?,
                    description = ?,
                    custom_url = ?,
                    uploads = ?,
                    updated = ?
        ''', (
            channel.id, channel.title, channel.description, channel.custom_url, uploads.id, updated,
            channel.title, channel.description, channel.custom_url, uploads.id, updated
        ))
        await self.con.execute('''
            INSERT OR REPLACE INTO youtube_handles
                VALUES (?, ?)
        ''', (channel.custom_url, channel.id))
        await self.con.executemany('''
            INSERT OR REPLACE INTO youtube_avatars
                VALUES (?, ?, ?, ?, ?)
        ''', [
            (channel.id, t.name, t.width, t.height, t.url)
            for t in channel.thumbnails
        ])

        channel = await self.get_channel_by_handle(channel.custom_url)

        await channel.add_playlist(uploads)
        await asyncio.gather(*(
            channel.add_playlist(c, uploads, n)
            for n, c, in uploads.children.items()
        ))

        return channel

    async def get_playlist(self, id: str) -> Playlist | None:
        async for row in await self.con.execute('''
            SELECT *
            FROM youtube_playlists
            WHERE id = ?
        ''', (id,)):
            return Playlist(self, *row)

    async def get_video(self, id: str) -> Video | None:
        async for row in await self.con.execute('''
            SELECT *
            FROM youtube_videos
            WHERE id = ?
        ''', (id,)):
            return Video(self, *row)

    async def outdated_files(self, added) -> list[File]:
        return [
            File(self, row[0], row[1], Path(row[2]), row[3])
            async for row in await self.con.execute('''
                SELECT *
                FROM youtube_video_files
                WHERE added < ?
            ''', (added,))
        ]
