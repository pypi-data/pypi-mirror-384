# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""VACUUM tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprLiteral, Query, Table

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_simple(txn: Transaction) -> None:
    """Test vacuum statement."""
    await txn.execute('ROLLBACK')

    query = Query().vacuum()
    assert query.__getsql__() == ('VACUUM', ())
    await txn.exq(query)

    await txn.execute('BEGIN TRANSACTION')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_schema_or_table(txn: Transaction) -> None:
    """Test vacuum statement."""
    tbl = Table('main')
    await txn.exq(Query().create_table(tbl).column('id', 'INTEGER'))
    await txn.execute('COMMIT')

    query = Query().vacuum(schema='main')
    assert query.__getsql__() == ('VACUUM "main"', ())
    await txn.exq(query)

    await txn.execute('BEGIN TRANSACTION')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_into(txn: Transaction) -> None:
    """Test vacuum statement."""
    tbl = Table('main')
    await txn.exq(Query().create_table(tbl).column('id', 'INTEGER'))
    await txn.execute('COMMIT')

    query = Query().vacuum(schema='main', into='file:bar.db?mode=memory')
    assert query.__getsql__() == ('VACUUM "main" INTO ?', ('file:bar.db?mode=memory',))
    await txn.exq(query)

    query = Query().vacuum(into=ExprLiteral('file:bar').strconcat('.db?mode=memory'))
    assert query.__getsql__() == ('VACUUM INTO ? || ?', ('file:bar', '.db?mode=memory'))
    await txn.exq(query)

    await txn.execute('BEGIN TRANSACTION')
