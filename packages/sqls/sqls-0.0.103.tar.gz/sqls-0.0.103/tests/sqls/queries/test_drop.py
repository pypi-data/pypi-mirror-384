# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""DROP tests."""

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
        Query().create_table(tbl).column('id', 'INTEGER').primary_key(),
    )


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='syntax not implemented')),
    ],
    indirect=True,
)
async def test_drop_index(txn: Transaction) -> None:
    """Test drop statements."""
    tbl = Table('tbl')
    idx = Table('idx')
    await txn.exq(Query().create_index(idx, tbl, tbl.id))

    query = Query().drop_index(idx)
    assert query.__getsql__()[0] == 'DROP INDEX "idx"'
    await txn.exq(query)

    query = Query().drop_index(idx, if_exists=True)
    assert query.__getsql__()[0] == 'DROP INDEX IF EXISTS "idx"'
    await txn.exq(query)


async def test_drop_table(txn: Transaction) -> None:
    """Test drop statements."""
    tbl = Table('tbl')
    query = Query().drop_table(tbl)
    assert query.__getsql__()[0] == 'DROP TABLE "tbl"'
    await txn.exq(query)

    query = Query().drop_table(tbl, if_exists=True)
    assert query.__getsql__()[0] == 'DROP TABLE IF EXISTS "tbl"'
    await txn.exq(query)


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_drop_trigger(txn: Transaction) -> None:
    """Test drop statements."""
    tbl = Table('tbl')
    trig = Table('trig')
    assert (
        await txn.exq(
            Query()
            .create_trigger(trig)
            .delete()
            .on_(tbl)
            .statements(
                Query().insert(tbl).columns(tbl.id).values((tbl.id,)),
            ),
        )
        == []
    )
    query = Query().drop_trigger(trig)
    assert query.__getsql__()[0] == 'DROP TRIGGER "trig"'
    await txn.exq(query)

    query = Query().drop_trigger(trig, if_exists=True)
    assert query.__getsql__()[0] == 'DROP TRIGGER IF EXISTS "trig"'
    await txn.exq(query)


async def test_drop_view(txn: Transaction) -> None:
    """Test drop statements."""
    tbl = Table('tbl')
    view = Table('vw_')
    await txn.exq(Query().create_view(view).as_(Query().select(tbl.id.typed(int)).from_(tbl)))

    query = Query().drop_view(view)
    assert query.__getsql__()[0] == 'DROP VIEW "vw_"'
    await txn.exq(query)

    query = Query().drop_view(view, if_exists=True)
    assert query.__getsql__()[0] == 'DROP VIEW IF EXISTS "vw_"'
    await txn.exq(query)
