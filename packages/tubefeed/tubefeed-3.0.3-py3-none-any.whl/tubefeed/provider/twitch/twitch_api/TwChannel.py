from datetime import datetime

from . import Twitch
from .TwVideo import TwVideo


class TwChannel:
    def __init__(self,
                 twitch: Twitch,
                 id: str, login: str, display_name: str,
                 type: str, broadcaster_type: str,
                 description: str, profile_image_url: str, offline_image_url: str,
                 view_count: int,
                 created_at: datetime):
        self._twitch: Twitch = twitch

        self.id: str = id
        self.login: str = login
        self.display_name: str = display_name
        self.type: str = type
        self.broadcaster_type: str = broadcaster_type
        self.description: str = description
        self.profile_image_url: str = profile_image_url
        self.offline_image_url: str = offline_image_url
        self.view_count: int = view_count
        self.created_at: datetime = created_at

    @property
    def url(self) -> str:
        return f'https://twitch.tv/{self.login}'

    async def get_videos(self, type: str = TwVideo.TYPE_ALL, limit: int = 100) -> list[TwVideo]:
        # TODO handle pagination
        result = await self._twitch.get('/videos', user_id=self.id, type=type, first=limit)
        return [
            TwVideo(
                video['id'],
                video['stream_id'],
                video['title'],
                video['description'],
                datetime.strptime(video['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                datetime.strptime(video['published_at'], '%Y-%m-%dT%H:%M:%SZ'),
                video['thumbnail_url'],
                video['viewable'],
                video['view_count'],
                video['language'],
                video['type'],
                TwVideo.parse_video_duration(video['duration'])
            )
            for video in result['data']
        ]
