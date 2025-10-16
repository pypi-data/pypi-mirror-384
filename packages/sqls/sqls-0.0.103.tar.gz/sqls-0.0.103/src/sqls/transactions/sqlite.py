# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQLite manager."""

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

import aiosqlite

from .exceptions import IntegrityError, OperationalError

if TYPE_CHECKING:
    import sys
    from collections.abc import AsyncGenerator
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

    def __init__(self, connection: Connection) -> None:
        """Initialzize transaction object."""
        self.connection = connection

    async def execute(
        self,
        query: str,
        *args: BindArg,
    ) -> list[tuple[SqlValue, ...]]:
        """Execute query."""
        cursor = self.connection.cursor
        assert cursor
        await cursor.execute(query, args)
        return await cursor.fetchall()  # type: ignore[return-value]

    async def exq(self, query: Query[T]) -> list[T]:
        """Execute shorthand."""
        cursor = self.connection.cursor
        assert cursor
        try:
            assert (
                self.connection.immediate
                or 'SELECT' in query.__getsql__()[0]
                or 'ATTACH' in query.__getsql__()[0]
            )
            await cursor.execute(*query.__getsql__())
        except sqlite3.IntegrityError as err:
            msg = f'QUERY: {query.__getsql__()!r}, ERROR {err.args!r}.'
            raise IntegrityError(msg) from None
        except sqlite3.OperationalError as err:
            msg = f'QUERY: {query.__getsql__()!r}, ERROR {err.args!r}.'
            raise OperationalError(msg) from None

        return await cursor.fetchall()  # type: ignore[return-value]

    async def exq_count(self, query: SupportsGetsql) -> int:
        """Execute count shorthand."""
        cursor = self.connection.cursor
        assert cursor
        assert self.connection.immediate or 'SELECT' in query.__getsql__()[0]
        await cursor.execute(*query.__getsql__())
        if cursor.rowcount == -1:
            return len(await cursor.fetchall())  # type: ignore[arg-type]
        return cursor.rowcount

    async def __aenter__(self) -> Self:
        """Transaction setup."""
        assert self.connection.cursor
        await self.connection.cursor.execute(f'SAVEPOINT "{id(self)}"')
        return self.__class__(self.connection)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Transaction cleanup."""
        if exc is not None:
            await self.connection.connection.execute(
                f'ROLLBACK TRANSACTION TO SAVEPOINT "{id(self)}"',
            )
            raise exc
        await self.connection.connection.execute(f'RELEASE SAVEPOINT "{id(self)}"')
        return False


class Connection:
    """Sqlite connection."""

    def __init__(self, connection: aiosqlite.Connection) -> None:
        """Initialize."""
        self.connection = connection
        self.cursor: aiosqlite.Cursor | None = None
        self.immediate = False

    async def close(self) -> None:
        """Close connection."""
        await self.connection.close()

    async def __aenter__(self) -> Transaction:
        """Transaction setup."""
        self.cursor = await self.connection.cursor()
        await self.cursor.execute(f'BEGIN {"IMMEDIATE " if self.immediate else ""}TRANSACTION')
        return Transaction(self)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Transaction cleanup."""
        assert self.cursor
        if exc is not None:
            await self.cursor.execute('ROLLBACK TRANSACTION')
            await self.cursor.close()
            self.cursor = None
            raise exc
        await self.cursor.execute('COMMIT TRANSACTION')
        await self.cursor.close()
        return False


class Manager:
    """Database manager."""

    def __init__(self, uri: str, options: ManagerOptions | None = None) -> None:
        """Initialize."""
        self.uri = uri
        if not options:
            options = cast('ManagerOptions', {})
        self.max_connections = options.get('max_connections', 4)
        self.init_pragmas = options.get('init_pragmas', [])
        self.fini_pragmas = options.get('fini_pragmas', [])

        self.queue: asyncio.Queue[Connection] = asyncio.Queue()
        self.pool: list[Connection | None] = []

    async def init(self) -> None:
        """Initialize pool."""

    async def get_connection(self) -> Connection:
        """Create or retrieve a connection object."""
        if not self.queue.qsize() and len(self.pool) < self.max_connections:
            index = len(self.pool)
            self.pool.append(None)
            connection = Connection(await aiosqlite.connect(self.uri, uri=True))
            await connection.connection.execute('PRAGMA foreign_keys = ON')
            await connection.connection.execute('PRAGMA journal_mode = WAL')
            await connection.connection.execute('PRAGMA synchronous = normal')
            for pragma in self.init_pragmas:
                await connection.connection.execute(pragma)
            self.pool[index] = connection
            return connection

        return await self.queue.get()

    async def close(self) -> None:
        """Close all database connections."""
        for connection in self.pool:
            assert connection
            for pragma in self.fini_pragmas:
                await connection.connection.execute(pragma)
            await connection.close()

    @asynccontextmanager
    async def txn(self, immediate: bool = False) -> AsyncGenerator[Transaction, None]:
        """Open a transaction for database operations."""
        connection = await self.get_connection()
        connection.immediate = immediate
        try:
            async with connection as newtxn:
                yield newtxn
                newtxn.connection = None  # type: ignore[assignment]
        finally:
            await self.queue.put(connection)
