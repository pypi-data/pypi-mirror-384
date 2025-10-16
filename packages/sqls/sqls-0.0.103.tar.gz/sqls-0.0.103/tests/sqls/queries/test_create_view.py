# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""CREATE VIEW tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import Query, Table

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.fixture(autouse=True)
async def _autotable(txn: Transaction) -> None:
    tbl = Table('tbl')
    await txn.exq(
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key(autoincrement=True)
        .column('name', 'TEXT'),
    )


async def test_simple(txn: Transaction) -> None:
    """Test create view statement."""
    tbl = Table('tbl')
    view = Table('vw_')

    await txn.exq(
        Query()
        .create_view(view)
        .as_(
            Query().select(tbl.id.typed(int), tbl.name.typed(str)).from_(tbl),
        ),
    )
    assert not await txn.exq(Query().select(view.id.typed(int), view.name.typed(str)).from_(view))
    await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',), ('bar',)))
    assert await txn.exq(Query().select(view.id.typed(int), view.name.typed(str)).from_(view)) == [
        (1, 'foo'),
        (2, 'bar'),
    ]


async def test_column_names(txn: Transaction) -> None:
    """Test create view statement."""
    tbl = Table('tbl')
    view = Table('vw_')

    await txn.exq(
        Query()
        .create_view(view)
        .columns(view.name, view.id)
        .as_(
            Query().select(tbl.name.typed(int), tbl.id.typed(str)).from_(tbl),
        ),
    )
    assert not await txn.exq(Query().select(view.id.typed(int), view.name.typed(str)).from_(view))
    await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',), ('bar',)))
    assert await txn.exq(Query().select(view.id.typed(int), view.name.typed(str)).from_(view)) == [
        (1, 'foo'),
        (2, 'bar'),
    ]
