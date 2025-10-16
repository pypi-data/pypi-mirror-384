from pathlib import Path

import aiosqlite


class BaseDB:
    # TODO global DATABASE_PATH

    def __init__(self, path: Path):
        self._path: Path = path

    async def __aenter__(self) -> 'BaseDB':
        self.con: aiosqlite.Connection = await aiosqlite.connect(self._path)
        await self.con.execute('PRAGMA foreign_keys = ON')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

        await self.con.__aexit__(exc_type, exc_val, exc_tb)

    async def commit(self):
        await self.con.commit()

    async def rollback(self):
        await self.con.rollback()

    async def create_tables(self):
        pass
