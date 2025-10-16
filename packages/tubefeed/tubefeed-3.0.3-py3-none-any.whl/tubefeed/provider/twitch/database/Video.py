from datetime import datetime
from pathlib import Path

from . import Database
from .File import File


class Video:
    def __init__(self,
                 db: Database,
                 id: str, channel_id: str,
                 title: str, description: str, published_at: datetime, thumbnail_url: str,
                 duration: int):
        self._db: Database = db
        self.id: str = id
        self.channel_id: str = channel_id
        self.title: str = title
        self.description: str = description
        self.published_at: datetime = published_at
        self.thumbnail_url: str = thumbnail_url
        self.duration: int = duration

    @property
    def url(self) -> str:
        return f'https://www.twitch.tv/videos/{self.id}'

    async def get_file(self, extension: str) -> File | None:
        async for row in await self._db.con.execute('''
            SELECT *
            FROM twitch_video_files
            WHERE video = ? AND extension = ?
        ''', (self.id, extension)):
            return File(self._db, row[0], row[1], Path(row[2]), row[3])

    async def set_file(self, path: Path, extension: str) -> File:
        added = datetime.now()

        await self._db.con.execute('''
            INSERT INTO twitch_video_files
            VALUES (?, ?, ?, ?)
        ''', (self.id, extension, str(path), added))

        return File(self._db, self.id, extension, path, added)
