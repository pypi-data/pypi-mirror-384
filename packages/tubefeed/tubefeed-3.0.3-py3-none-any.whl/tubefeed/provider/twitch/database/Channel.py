from datetime import datetime

from . import Database
from .Video import Video
from ..twitch_api import TwVideo


class Channel:
    def __init__(self,
                 db: Database,
                 id: str, login: str, display_name: str, description: str, profile_image_url: str,
                 updated: datetime):
        self._db: Database = db
        self.id: str = id
        self.login: str = login
        self.display_name: str = display_name
        self.description: str = description
        self.profile_image_url: str = profile_image_url
        self.updated: datetime = updated

    @property
    def url(self) -> str:
        return f'https://twitch.tv/{self.login}'

    async def add_video(self, video: TwVideo) -> Video:
        await self._db.con.execute('''
            INSERT INTO twitch_videos
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id)
                DO UPDATE SET
                    title = ?,
                    description = ?,
                    published_at = ?,
                    thumbnail_url = ?,
                    duration = ?
        ''', (
            video.id, self.id, video.title, video.description, video.published_at, video.thumbnail_url, video.duration,
            video.title, video.description, video.published_at, video.thumbnail_url, video.duration
        ))

        return Video(self._db,
                     video.id, self.id,
                     video.title, video.description, video.published_at, video.thumbnail_url,
                     video.duration)
