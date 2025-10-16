from datetime import datetime

from aiohttp import ClientSession

from .TwChannel import TwChannel


class Twitch:
    def __init__(self, client_id: str, client_secret: str):
        self._client_id: str = client_id
        self._client_secret: str = client_secret

    async def __aenter__(self) -> 'Twitch':
        self._session: ClientSession = ClientSession()

        async with self._session.post(
                'https://id.twitch.tv/oauth2/token',
                data={
                    'client_id': self._client_id,
                    'client_secret': self._client_secret,
                    'grant_type': 'client_credentials'
                }
        ) as response:
            data = await response.json()
            self._access_token: str = data['access_token']

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    async def get(self, path: str, **params) -> dict | list:
        query = '&'.join(f'{k}={v}' for k, v in params.items())

        async with self._session.get(f'https://api.twitch.tv/helix{path}?{query}', headers={
            'Client-Id': self._client_id,
            'Authorization': f'Bearer {self._access_token}'
        }) as response:
            result = await response.json()
            return result

    async def _get_channel(self, **params) -> TwChannel | None:
        result = await self.get('/users', **params)

        for channel in result['data']:
            return TwChannel(
                self,
                channel['id'],
                channel['login'],
                channel['display_name'],
                channel['type'],
                channel['broadcaster_type'],
                channel['description'],
                channel['profile_image_url'],
                channel['offline_image_url'],
                channel['view_count'],
                datetime.strptime(channel['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            )

        return None

    async def get_channel_by_name(self, name: str) -> TwChannel | None:
        return await self._get_channel(login=name)

    async def get_channel_by_id(self, id: str) -> TwChannel | None:
        return await self._get_channel(id=id)
