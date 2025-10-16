# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Postgresql manager tests."""

from __future__ import annotations

from contextlib import suppress
from os import getenv
from typing import TYPE_CHECKING, cast

import pytest

from sqls.transactions import IntegrityError, OperationalError, get_manager

from .common import Query

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqls.interfaces import Manager
    from sqls.transactions.postgresql import Manager as PostgresqlManager


@pytest.fixture
async def manager() -> AsyncGenerator[Manager, None]:
    """In memory database manager."""
    host = getenv('SQLS_POSTGRES_HOST', 'localhost')
    res = get_manager(f'postgresql://sqlsuser:sqlspass@{host}/sqls')
    await res.init()
    async with res.pool.acquire() as connection:  # type: ignore[attr-defined]
        await connection.fetch('DROP SCHEMA public CASCADE')
        await connection.fetch('CREATE SCHEMA public')
    yield res
    await res.close()


def test_options() -> None:
    """Test options are set on manager."""
    host = getenv('SQLS_POSTGRES_HOST', 'localhost')
    res = cast(
        'PostgresqlManager',
        get_manager(
            f'postgresql://sqlsuser:sqlspass@{host}/sqls',
            {'max_connections': 2},
        ),
    )
    assert res.max_connections == 2


async def test_manager(manager: PostgresqlManager) -> None:
    """Test Manager."""
    async with manager.txn() as txn, manager.txn() as inner_txn:
        assert inner_txn != txn

    async with manager.txn() as txn:
        await txn.execute('SELECT 1')
        assert await txn.exq_count(Query('SELECT 1')) == 1
        assert await txn.exq(Query('SELECT 1')) == [(1,)]

        assert await txn.exq(Query('SELECT ?', 1)) == [(1,)]
        assert await txn.exq(Query('SELECT ?', 1.0)) == [(1.0,)]
        assert await txn.exq(Query('SELECT ?', 'foo')) == [('foo',)]

    async with manager.txn() as txn:
        await txn.exq(Query('CREATE TABLE foo (bar INTEGER PRIMARY KEY)'))
        with pytest.raises(IntegrityError, match='unique constraint'):
            await txn.exq(Query('INSERT INTO foo (bar) VALUES(1),(1)'))

    with pytest.raises(OperationalError, match='syntax error'):
        async with manager.txn() as txn:
            await txn.exq(Query('BAD SYNTAX'))

    async with manager.txn() as txn:
        await txn.exq(Query('CREATE TABLE foo (bar INTEGER PRIMARY KEY)'))
        with suppress(ValueError):
            async with txn as innertxn:
                await innertxn.exq(Query('INSERT INTO foo (bar) VALUES(1)'))
                raise ValueError
        async with txn as innertxn:
            assert await innertxn.exq(Query('INSERT INTO foo (bar) VALUES(1)')) == []
