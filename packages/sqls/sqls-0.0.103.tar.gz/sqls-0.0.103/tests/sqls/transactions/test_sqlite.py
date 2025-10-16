# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Sqlite manager tests."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, patch

import pytest

from sqls.transactions import IntegrityError, OperationalError, get_manager

from .common import Query

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqls.interfaces import Manager
    from sqls.transactions.sqlite import Manager as SqliteManager


@pytest.fixture
async def manager() -> AsyncGenerator[Manager, None]:
    """In memory database manager."""
    res = get_manager('file:memdb1?mode=memory&cache=shared')
    await res.init()
    yield res
    await res.close()


async def test_options() -> None:
    """Test options are set on manager."""
    res = cast(
        'SqliteManager',
        get_manager(
            'file:memdb1?mode=memory&cache=shared',
            {
                'max_connections': 2,
                'init_pragmas': ['PRAGMA foo'],
                'fini_pragmas': ['PRAGMA bar'],
            },
        ),
    )
    assert res.max_connections == 2
    with patch('aiosqlite.Connection.execute', new_callable=AsyncMock) as execute:
        await res.init()
        async with res.txn():
            pass
        assert execute.call_count == 4
        assert execute.call_args.args == ('PRAGMA foo',)
        await res.close()
        assert execute.call_count == 5
        assert execute.call_args.args == ('PRAGMA bar',)


async def test_manager(manager: SqliteManager) -> None:
    """Test Manager."""
    assert len(manager.pool) == 0

    async with manager.txn() as txn:
        assert txn
    assert len(manager.pool) == 1

    async with manager.txn() as txn, manager.txn() as inner_txn:
        assert inner_txn != txn
    assert len(manager.pool) == 2

    async with manager.txn() as txn:
        await txn.execute('SELECT 1')
        assert await txn.exq_count(Query('SELECT 1')) == 1
        assert await txn.exq(Query('SELECT 1')) == [(1,)]

    with pytest.raises(IntegrityError, match='UNIQUE'):  # noqa: PT012
        async with manager.txn(True) as txn:
            await txn.exq(Query('CREATE TABLE foo (bar INTEGER PRIMARY KEY)'))
            assert await txn.exq_count(Query('INSERT INTO foo (bar) VALUES(1),(2)')) == 2
            await txn.exq(Query('INSERT INTO foo (bar) VALUES(1)'))

    with pytest.raises(OperationalError, match='syntax error'):
        async with manager.txn(True) as txn:
            await txn.exq(Query('BAD SYNTAX'))

    async with manager.txn(True) as txn:
        await txn.exq(Query('CREATE TABLE foo (bar INTEGER PRIMARY KEY)'))
        with suppress(ValueError):
            async with txn as innertxn:
                await innertxn.exq(Query('INSERT INTO foo (bar) VALUES(1)'))
                raise ValueError
        async with txn as innertxn:
            assert await innertxn.exq(Query('INSERT INTO foo (bar) VALUES(1)')) == []
