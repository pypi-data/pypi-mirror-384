from typing import Iterator, Callable, Coroutine, TypeAlias

from aiohttp.web import Request, Response, StreamResponse

from ..database import BaseDB

HANDLER_TYPE: TypeAlias = Callable[[Request], Coroutine[None, None, Response | StreamResponse]]


class Provider:
    PROVIDER_NAME = None

    @property
    def database_class(self) -> type[BaseDB]:
        raise BaseDB

    @property
    def routes(self) -> Iterator[tuple[list[str], str, HANDLER_TYPE]]:
        raise NotImplementedError

    def url(self, request: Request, path: str) -> str:
        return f'{request.scheme}://{request.host}/{self.PROVIDER_NAME}{path}'
