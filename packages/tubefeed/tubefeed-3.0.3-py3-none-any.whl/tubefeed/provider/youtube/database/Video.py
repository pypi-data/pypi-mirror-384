from datetime import datetime
from pathlib import Path

from . import Database
from .File import File
from .Thumbnail import Thumbnail


class Video:
    def __init__(self, db: Database, id: str, title: str, description: str, published: str, duration: int):
        self._db: Database = db

        self.id: str = id
        self.title: str = title
        self.description: str = description
        self.published: datetime = datetime.strptime(published, '%Y-%m-%d %H:%M:%S')
        self.duration: int = duration

    @property
    def url(self) -> str:
        return f'https://www.youtube.com/watch?v={self.id}'

    async def thumbnails(self) -> list[Thumbnail]:
        return [
            Thumbnail(*row)
            async for row in await self._db.con.execute('''
                SELECT name, width, height, url
                FROM youtube_video_thumbnails
                WHERE video = ?
            ''', (self.id,))
        ]

    async def get_file(self, extension: str) -> File | None:
        async for row in await self._db.con.execute('''
            SELECT *
            FROM youtube_video_files
            WHERE video = ? AND extension = ?
        ''', (self.id, extension)):
            return File(self._db, row[0], row[1], Path(row[2]), row[3])

    async def set_file(self, path: Path, extension: str) -> File:
        added = datetime.now()

        await self._db.con.execute('''
            INSERT INTO youtube_video_files
            VALUES (?, ?, ?, ?)
        ''', (self.id, extension, str(path), added))

        return File(self._db, self.id, extension, path, added)
