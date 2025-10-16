# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Squal tests."""

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
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_attach_detach(txn: Transaction) -> None:
    """Test attach/detach statement."""
    tbl = Table('tbl')
    atbl = Table('atbl', schema='attached')
    await txn.exq(
        Query().create_table(tbl).column('id', 'INTEGER').primary_key().column('name', 'TEXT'),
    )
    await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',)))

    query = Query().attach(ExprLiteral(':memory:'), 'attached')
    assert await txn.exq(query) == []

    query = Query().create_table(atbl).column('id', 'INTEGER').primary_key().column('name', 'TEXT')
    assert await txn.exq(query) == []

    query = Query().insert(atbl).columns(atbl.name).values(('bar',))
    assert await txn.exq(query) == []

    assert await txn.exq(Query().select(atbl.name.typed(str)).from_(atbl)) == [('bar',)]

    await txn.execute('COMMIT')
    await txn.execute('BEGIN')

    query = Query().detach('attached')
    assert await txn.exq(query) == []

    with pytest.raises(Exception, match='no such table') as exc:
        assert await txn.exq(Query().select(atbl.name.typed(str)).from_(atbl))
    assert 'no such table' in str(exc)
