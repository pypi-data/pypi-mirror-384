# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Queries test fixtures."""

from __future__ import annotations

import warnings
from os import getenv
from typing import TYPE_CHECKING

import pytest

from sqls.transactions import get_manager

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqls.interfaces import Transaction


@pytest.fixture(params=['sqlite', 'postgres', 'mysql'])
async def txn(request: pytest.FixtureRequest) -> AsyncGenerator[Transaction, None]:
    """Transaction fixture."""
    if request.param == 'sqlite':
        manager = get_manager(':memory:')
        async with manager.txn(True) as transaction:
            yield transaction
        await manager.close()
    elif request.param == 'postgres':
        host = getenv('SQLS_POSTGRES_HOST', 'localhost')
        manager = get_manager(f'postgresql://sqlsuser:sqlspass@{host}/sqls')
        await manager.init()
        async with manager.pool.acquire() as connection:  # type: ignore[attr-defined]
            await connection.fetch('DROP SCHEMA public CASCADE')
            await connection.fetch('CREATE SCHEMA public')
        async with manager.txn() as transaction:
            yield transaction
        await manager.close()
    elif request.param == 'mysql':
        host = getenv('SQLS_MYSQL_HOST', 'localhost')
        manager = get_manager(f'mysql://sqlsuser:sqlspass@{host}:3306/sqls')
        await manager.init()
        warnings.filterwarnings('ignore', module='aiomysql')
        async with manager.txn() as transaction:
            await transaction.execute('DROP TABLE IF EXISTS `tbl` CASCADE')
            await transaction.execute('DROP TABLE IF EXISTS `dst` CASCADE')
            await transaction.execute('DROP VIEW IF EXISTS `vw_` CASCADE')
        async with manager.txn() as transaction:
            yield transaction
        await manager.close()
        warnings.filterwarnings('default', module='aiomysql')
