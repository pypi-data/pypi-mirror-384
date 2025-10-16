# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""PostgreSQL manager."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import asyncpg  # type: ignore[import-untyped]

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

    def __init__(self, connection: asyncpg.Connection) -> None:
        """Initialzize transaction object."""
        self.connection = connection

    async def execute(self, query: str, *args: BindArg) -> list[tuple[SqlValue, ...]]:
        """Execute query."""
        return await self.connection.fetch(query, *args)  # type: ignore[no-any-return]

    async def exq(self, query: Query[T]) -> list[T]:
        """Execute shorthand."""
        qstr, args = query.__getsql__()

        idx = 1
        while '?' in qstr:
            if isinstance(args[idx - 1], int):
                subtyp = '::int'
            elif isinstance(args[idx - 1], float):
                subtyp = '::float'
            else:
                subtyp = ''

            qstr = qstr.replace('?', f'${idx}{subtyp}', 1)
            idx += 1

        # fixups
        qstr = qstr.replace('"id" INTEGER', '"id" SERIAL')
        qstr = qstr.replace(' AUTOINCREMENT', '')
        qstr = qstr.replace(' INTEGER DEFAULT TRUE', 'BOOLEAN DEFAULT TRUE')
        qstr = qstr.replace(' INTEGER DEFAULT FALSE', 'BOOLEAN DEFAULT FALSE')
        qstr = qstr.replace(' VIRTUAL', ' STORED')
        qstr = qstr.replace('REINDEX', 'REINDEX TABLE')
        qstr = qstr.replace('NOT REGEXP', '!~')
        qstr = qstr.replace('REGEXP', '~')
        qstr = qstr.replace('group_concat', 'string_agg')

        try:
            return await self.connection.fetch(qstr, *args)  # type: ignore[no-any-return]
        except asyncpg.exceptions.UniqueViolationError as err:
            msg = f'QUERY: {query.__getsql__()!r}, ERROR {err.args!r}.'
            raise IntegrityError(msg) from None
        except asyncpg.exceptions.PostgresError as err:
            msg = f'QUERY: {query.__getsql__()!r}, ERROR {err.args!r}.'
            raise OperationalError(msg) from None

    async def exq_count(self, query: SupportsGetsql) -> int:
        """Execute shorthand."""
        return len(await self.exq(cast('Query[None]', query)))

    async def __aenter__(self) -> Self:
        """Transaction setup."""
        await self.connection.execute(f'SAVEPOINT "{id(self)}"')
        return self.__class__(self.connection)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Transaction cleanup."""
        if exc is not None:
            await self.connection.execute(f'ROLLBACK TO SAVEPOINT "{id(self)}"')
            raise exc
        await self.connection.execute(f'RELEASE SAVEPOINT "{id(self)}"')
        return False


class Manager:
    """Database manager."""

    def __init__(self, uri: str, options: ManagerOptions | None = None) -> None:
        """Initialize."""
        self.uri = uri
        if not options:
            options = cast('ManagerOptions', {})
        self.max_connections = options.get('max_connections', 4)
        self.pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        """Initialize pool."""
        parsed = urlparse(self.uri)
        self.pool = await asyncpg.create_pool(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],
            min_size=min(self.max_connections, 10),
            max_size=self.max_connections,
        )

    async def close(self) -> None:
        """Close all database connections."""
        assert self.pool
        await self.pool.close()

    @asynccontextmanager
    async def txn(self, _: bool = False) -> AsyncGenerator[Transaction, None]:
        """Open a transaction for database operations."""
        assert self.pool
        async with self.pool.acquire() as connection, connection.transaction():
            yield Transaction(connection)
