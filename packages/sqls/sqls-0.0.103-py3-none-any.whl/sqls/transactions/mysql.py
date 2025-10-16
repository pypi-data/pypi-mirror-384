# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""MySQL manager."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import aiomysql  # type: ignore[import-untyped]

from .exceptions import IntegrityError, OperationalError

if TYPE_CHECKING:
    import sys
    from collections.abc import AsyncIterator
    from types import TracebackType
    from typing import TypeVar

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    from sqls.interfaces import BindArg, ManagerOptions, Query, SqlValue, SupportsGetsql

    T = TypeVar('T')


class Transaction:
    """Transaction class."""

    def __init__(self, cursor: aiomysql.Cursor) -> None:
        """Initialzize transaction object."""
        self.cursor = cursor

    async def execute(self, query: str, *args: BindArg) -> list[tuple[SqlValue, ...]]:
        """Execute query."""
        return await self.cursor.execute(query, args)  # type: ignore[no-any-return]

    async def exq(self, query: Query[T]) -> list[T]:
        """Execute shorthand."""
        qstr, args = query.__getsql__()
        qstr = qstr.replace('?', '%s')

        # fixups
        qstr = qstr.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
        qstr = qstr.replace('DEFAULT VALUES', 'VALUES ()')
        qstr = qstr.replace('INSERT OR IGNORE', 'INSERT IGNORE')
        qstr = qstr.replace('UPDATE OR IGNORE', 'UPDATE IGNORE')
        qstr = qstr.replace('AS TEXT', 'AS CHAR')
        qstr = qstr.replace(' % ', ' MOD ')

        try:
            await self.cursor.execute(qstr, args)
        except aiomysql.IntegrityError as err:
            msg = f'QUERY: {query.__getsql__()!r}, ERROR {err.args!r}.'
            raise IntegrityError(msg) from None
        except aiomysql.Error as err:
            msg = f'QUERY: {query.__getsql__()!r}, ERROR {err.args!r}.'
            raise OperationalError(msg) from None

        return list(await self.cursor.fetchall())

    async def exq_count(self, query: SupportsGetsql) -> int:
        """Execute shorthand."""
        return len(await self.exq(cast('Query[None]', query)))

    async def __aenter__(self) -> Self:
        """Transaction setup."""
        await self.cursor.execute(f'SAVEPOINT x{id(self)}')
        return self.__class__(self.cursor)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Transaction cleanup."""
        if exc is not None:
            await self.cursor.execute(f'ROLLBACK TO SAVEPOINT x{id(self)}')
            raise exc
        await self.cursor.execute(f'RELEASE SAVEPOINT x{id(self)}')
        return False


class Manager:
    """Database manager."""

    def __init__(self, uri: str, options: ManagerOptions | None = None) -> None:
        """Initialize."""
        self.uri = uri
        if not options:
            options = cast('ManagerOptions', {})
        self.max_connections = options.get('max_connections', 4)
        self.pool: aiomysql.Pool | None = None

    async def init(self) -> None:
        """Initialize pool."""
        parsed = urlparse(self.uri)
        self.pool = await aiomysql.create_pool(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            db=parsed.path[1:],
            maxsize=self.max_connections,
            sql_mode='ANSI',
        )

    async def close(self) -> None:
        """Close all database connections."""
        assert self.pool
        self.pool.close()
        await self.pool.wait_closed()

    @asynccontextmanager
    async def txn(self, _: bool = False) -> AsyncIterator[Transaction]:
        """Open a transaction for database operations."""
        assert self.pool

        connection = await self.pool.acquire()
        cursor = await connection.cursor()
        await cursor.execute('START TRANSACTION')
        try:
            yield Transaction(cursor)
        except Exception:
            await cursor.execute('ROLLBACK')
            raise
        else:
            await cursor.execute('COMMIT')
        finally:
            await cursor.close()
            await self.pool.release(connection)
