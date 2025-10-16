import logging
import os
from pathlib import Path

from aiohttp import web

from . import APP_VERSION, DB_VERSION
from .database import BaseDB
from .provider import Provider
from .provider.twitch import TwitchProvider
from .provider.youtube import YouTubeProvider

DEBUG = os.environ.get('DEBUG', '').lower() in ('true', 'yes', '1')
if DEBUG:
    logging.warning('--- DEBUG MODE IS ENABLED ---')


# default routes
async def root(request: web.Request) -> web.Response:
    return web.json_response({
        'title': 'Tubefeed',
        'version': APP_VERSION,
        'refs': {
            name: f'{request.scheme}://{request.host}/{name}'
            for name in request.app['providers']
        }
    })


async def provider_root(request: web.Request) -> web.Response:
    provider_name: str = request.match_info.get('provider')
    provider: Provider = request.app['providers'].get(provider_name, None)

    if provider is None:
        return web.HTTPNotFound()

    return web.json_response({
        'provider': provider_name,
        'refs': {
            handler.__name__: {
                'description': description,
                'schemas': [
                    f'{request.scheme}://{request.host}/{provider_name}{path}'
                    for path in paths
                ]
            }
            for paths, description, handler in provider.routes
        }
    })


# web server configuration
async def app_startup(app: web.Application):
    # get some configuration options
    data_dir = Path(os.environ.get('DATA_DIR', './data/'))
    logging.warning(f'using data directory at "{data_dir}"')

    version_path = data_dir / 'version.txt'
    database_path = data_dir / 'cache.db'

    download_dir = data_dir / 'downloads'
    logging.warning(f'using download directory at "{download_dir}"')

    app['database_path'] = database_path
    app['download_dir'] = download_dir

    # create data directory if it does not exist
    if not data_dir.exists():
        data_dir.mkdir(parents=True)

    # get database version from file
    if version_path.exists():
        with open(version_path, 'r') as f:
            current_version = f.read().strip()
    else:
        current_version = None

    # delete database if outdated
    if current_version != DB_VERSION or DEBUG:
        logging.warning(f'database schema is outdated, recreating')

        database_path.unlink(missing_ok=True)
        with open(version_path, 'w') as f:
            f.write(DB_VERSION)

        if download_dir.exists():
            for downloaded_file in download_dir.iterdir():
                downloaded_file.unlink()

            download_dir.rmdir()

    # create download directory
    download_dir.mkdir(exist_ok=True)

    # create default tables
    logging.warning('initializing database')

    async with BaseDB(database_path) as db:
        await db.create_tables()

    # initialize providers
    for name, provider in app['providers'].items():
        logging.warning(f'initializing database for provider {name}')

        async with provider.database_class(database_path) as db:
            await db.create_tables()


def main():
    app = web.Application()

    # add providers
    logging.warning('load video providers')

    app['providers'] = {
        YouTubeProvider.PROVIDER_NAME: YouTubeProvider(),
        TwitchProvider.PROVIDER_NAME: TwitchProvider(),
    }

    # add routes
    routes = web.RouteTableDef()

    routes.get('/')(root)
    routes.get('/{provider}')(provider_root)

    logging.warning('initialize provider routes')
    for name, provider in app['providers'].items():
        for paths, _, handler in provider.routes:
            for path in paths:
                routes.get(f'/{name}{path}')(handler)

    app.add_routes(routes)

    # add startup function
    # noinspection PyTypeChecker
    app.on_startup.append(app_startup)

    # start webserver
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))

    logging.warning(f'starting webserver at {host}:{port}')
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING if not DEBUG else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )

    main()
