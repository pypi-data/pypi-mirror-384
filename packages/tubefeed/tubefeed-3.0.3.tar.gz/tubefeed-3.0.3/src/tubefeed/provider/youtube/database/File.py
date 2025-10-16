from datetime import datetime
from pathlib import Path

from . import Database


class File:
    def __init__(self, db: Database, video_id: str, extension: str, path: Path, added: datetime):
        self._db: Database = db
        self.video_id: str = video_id
        self.extension: str = extension
        self.path: Path = path
        self.added: datetime = added

    async def delete(self):
        await self._db.con.execute('''
            DELETE FROM youtube_video_files
            WHERE video = ? AND extension = ?
        ''', (self.video_id, self.extension))
