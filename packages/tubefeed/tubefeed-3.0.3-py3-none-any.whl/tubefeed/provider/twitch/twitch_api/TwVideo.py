import re
from datetime import datetime


class TwVideo:
    TYPE_ALL = 'all'
    TYPE_ARCHIVE = 'archive'
    TYPE_HIGHLIGHT = 'highlight'
    TYPE_UPLOAD = 'upload'

    @staticmethod
    def parse_video_duration(duration: str) -> int:
        match = re.search(r'((\d+)h)?((\d+)m)?((\d+)s)?', duration)

        return sum(
            60 ** i * d
            for i, d in enumerate(
                int(d)
                for i, d in enumerate(reversed(match.groups()), start=1)
                if i % 2 and d is not None
            )
        )

    def __init__(self,
                 id: str, stream_id: str,
                 title: str, description: str, created_at: datetime, published_at: datetime,
                 thumbnail_url: str, viewable: str, view_count: int, language: str, type: str, duration: int):
        self.id: str = id
        self.stream_id: str = stream_id
        self.title: str = title
        self.description: str = description
        self.created_at: datetime = created_at
        self.published_at: datetime = published_at
        self.thumbnail_url: str = thumbnail_url
        self.viewable: str = viewable
        self.view_count: int = view_count
        self.language: str = language
        self.type: str = type
        self.duration: int = duration

    @property
    def url(self) -> str:
        return f'https://www.twitch.tv/videos/{self.id}'
