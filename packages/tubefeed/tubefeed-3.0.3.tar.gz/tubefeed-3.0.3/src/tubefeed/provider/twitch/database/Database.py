from datetime import datetime
from pathlib import Path

from .Channel import Channel
from .File import File
from .Video import Video
from ..twitch_api import TwChannel
from ....database import BaseDB


class Database(BaseDB):
    async def create_tables(self):
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS twitch_channels (
                id                 VARCHAR  PRIMARY KEY,
                login              VARCHAR  NOT NULL,
                display_name       VARCHAR  NOT NULL,
                description        VARCHAR  NOT NULL,
                profile_image_url  VARCHAR  NOT NULL,
                updated            DATETIME NOT NULL
            )
        ''')
        await self.con.execute('''
            CREATE INDEX IF NOT EXISTS idx_twitch_channels_login
            ON twitch_channels (login)
        ''')

        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS twitch_videos (
                id             VARCHAR  PRIMARY KEY,
                channel        VARCHAR  NOT NULL,
                title          VARCHAR  NOT NULL,
                description    VARCHAR  NOT NULL,
                published_at   DATETIME NOT NULL,
                thumbnail_url  VARCHAR  NOT NULL,
                duration       INTEGER  NOT NULL,
                FOREIGN KEY (channel) REFERENCES twitch_channels(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        await self.con.execute('''
            CREATE TABLE IF NOT EXISTS twitch_video_files (
                video     VARCHAR NOT NULL,
                extension VARCHAR NOT NULL,
                path      VARCHAR NOT NULL,
                added     DATETIME NOT NULL,
                PRIMARY KEY (video, extension),
                FOREIGN KEY (video) REFERENCES twitch_videos(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')

    async def get_channel_by_id(self, id: str) -> Channel | None:
        async for row in await self.con.execute('''
            SELECT *
            FROM twitch_channels
            WHERE id = ?
        ''', (id,)):
            return Channel(self, *row)

    async def get_channel_by_name(self, name: str) -> Channel | None:
        async for row in await self.con.execute('''
            SELECT *
            FROM twitch_channels
            WHERE login = ?
        ''', (name,)):
            return Channel(self, *row)

    async def add_channel(self, channel: TwChannel, updated: datetime) -> Channel:
        await self.con.execute('''
            INSERT INTO twitch_channels
                VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (id)
                DO UPDATE SET
                    login = ?,
                    display_name = ?,
                    description = ?,
                    profile_image_url = ?,
                    updated = ?
        ''', (
            channel.id, channel.login, channel.display_name, channel.description, channel.profile_image_url, updated,
            channel.login, channel.display_name, channel.description, channel.profile_image_url, updated
        ))

        return await self.get_channel_by_id(channel.id)

    async def get_video(self, id: str) -> Video | None:
        async for row in await self.con.execute('''
            SELECT *
            FROM twitch_videos
            WHERE id = ?
        ''', (id,)):
            return Video(self, *row)

    async def outdated_files(self, added) -> list[File]:
        return [
            File(self, row[0], row[1], Path(row[2]), row[3])
            async for row in await self.con.execute('''
                SELECT *
                FROM twitch_video_files
                WHERE added < ?
            ''', (added,))
        ]
