# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""REINDEX tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import Query, Table
from sqls.transactions.sqlite import Transaction as SqliteTransaction

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_simple(txn: Transaction) -> None:
    """Test reindex statement."""
    query = Query().reindex()
    assert query.__getsql__() == ('REINDEX', ())
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_table(txn: Transaction) -> None:
    """Test reindex statement."""
    tbl = Table('tbl')
    assert await txn.exq(Query().create_table(tbl).column('id', 'INTEGER')) == []

    query = Query().reindex('tbl')
    assert query.__getsql__() == ('REINDEX "tbl"', ())
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_schema_table(txn: Transaction) -> None:
    """Test reindex statement."""
    schema = 'main' if isinstance(txn, SqliteTransaction) else 'public'
    tbl = Table('tbl', schema=schema)
    assert await txn.exq(Query().create_table(tbl).column('id', 'INTEGER')) == []

    query = Query().reindex(tbl)
    assert query.__getsql__() == (f'REINDEX "{schema}"."tbl"', ())
    assert await txn.exq(query) == []
