# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Mysql manager tests."""

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
    from sqls.transactions.mysql import Manager as MysqlManager


@pytest.fixture
async def manager(recwarn: pytest.WarningsRecorder) -> AsyncGenerator[Manager, None]:
    """Test MySQL database manager."""
    host = getenv('SQLS_MYSQL_HOST', 'localhost')
    res = get_manager(f'mysql://sqlsuser:sqlspass@{host}:3306/sqls')
    await res.init()
    async with res.txn() as txn:
        await txn.execute('DROP TABLE IF EXISTS "foo" CASCADE')
    assert len(recwarn) <= 1
    yield res
    await res.close()


def test_options() -> None:
    """Test options are set on manager."""
    host = getenv('SQLS_MYSQL_HOST', 'localhost')
    res = cast(
        'MysqlManager',
        get_manager(
            f'mysql://sqlsuser:sqlspass@{host}:3306/sqls',
            {'max_connections': 2},
        ),
    )
    assert res.max_connections == 2


async def test_manager(manager: MysqlManager) -> None:
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

        await txn.exq(Query('CREATE TABLE foo (bar INTEGER PRIMARY KEY)'))

    with pytest.raises(IntegrityError, match='Duplicate entry'):
        async with manager.txn() as txn:
            await txn.exq(Query('INSERT INTO foo (bar) VALUES(1),(1)'))

    with pytest.raises(OperationalError, match='error in your SQL syntax'):
        async with manager.txn() as txn:
            await txn.exq(Query('BAD SYNTAX'))

    async with manager.txn() as txn:
        with suppress(ValueError):
            async with txn as inner_txn:
                await inner_txn.exq(Query('INSERT INTO foo (bar) VALUES(1)'))
                raise ValueError
        async with txn as inner_txn:
            assert await inner_txn.exq(Query('INSERT INTO foo (bar) VALUES(1)')) == []
