# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""CREATE INDEX tests."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprLiteral, Query, Table
from sqls.transactions import IntegrityError

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.fixture(autouse=True)
async def _autotable(txn: Transaction) -> None:
    tbl = Table('tbl')
    await txn.exq(
        Query().create_table(tbl).column('id', 'INTEGER').primary_key().column('name', 'TEXT'),
    )


async def test_simple(txn: Transaction) -> None:
    """Test create index statement."""
    tbl = Table('tbl')

    assert (
        await txn.exq(
            Query().create_index(Table('idx'), tbl, tbl.name),
        )
        == []
    )


async def test_if_not_exists(txn: Transaction) -> None:
    """Test create index statement."""
    tbl = Table('tbl')

    assert (
        await txn.exq(
            Query().create_index(Table('idx'), tbl, tbl.name, if_not_exists=True),
        )
        == []
    )


async def test_unique(txn: Transaction) -> None:
    """Test create index statement."""
    tbl = Table('tbl')

    assert (
        await txn.exq(
            Query().create_index(Table('idx'), tbl, tbl.name, unique=True),
        )
        == []
    )

    query = Query().insert(tbl).columns(tbl.name).values(('foo',))
    assert await txn.exq(query) == []

    with suppress(IntegrityError):
        async with txn as subtxn:  # type: ignore[attr-defined]
            with pytest.raises(IntegrityError) as err:
                await subtxn.exq(query)
            assert 'unique constraint' in str(err).lower() or 'duplicate entry' in str(err).lower()
            raise IntegrityError


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip('unsupported')),
    ],
    indirect=True,
)
async def test_partial(txn: Transaction) -> None:
    """Test create index statement."""
    tbl = Table('tbl')

    assert (
        await txn.exq(
            Query()
            .create_index(Table('pidx'), tbl, tbl.name)
            .where(tbl.name == ExprLiteral('42', bind=False)),
        )
        == []
    )
