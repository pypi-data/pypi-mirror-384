# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""UPDATE tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import Query, QueryError, Table

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
        .unique()
        .column('name', 'TEXT')
        .unique()
        .column('age', 'INTEGER'),
    )

    dst = Table('dst')
    await txn.exq(
        Query()
        .create_table(dst)
        .column('id', 'INTEGER')
        .primary_key()
        .column('name', 'TEXT')
        .column('age', 'INTEGER'),
    )

    await txn.exq(
        Query()
        .insert(tbl)
        .columns(tbl.name, tbl.age)
        .values(
            ('John', 42),
            ('Paul', 43),
            ('Ringo', 44),
            ('George', 45),
        ),
    )


async def test_column_all(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    with pytest.raises(QueryError, match='same length'):
        Query().update(tbl).set((tbl.age,), ())

    query = Query().update(tbl).set((tbl.age,), (42,))
    assert query.__getsql__() == ('UPDATE "tbl" SET "age"=?', (42,))
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_update_or_rollback(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update_or_rollback(tbl).set((tbl.age,), (42,))
    assert query.__getsql__() == ('UPDATE OR ROLLBACK "tbl" SET "age"=?', (42,))
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_update_or_abort(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update_or_abort(tbl).set((tbl.age,), (42,))
    assert query.__getsql__() == ('UPDATE OR ABORT "tbl" SET "age"=?', (42,))
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_update_or_replace(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update_or_replace(tbl).set((tbl.age,), (42,))
    assert query.__getsql__() == ('UPDATE OR REPLACE "tbl" SET "age"=?', (42,))
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_update_or_fail(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update_or_fail(tbl).set((tbl.age,), (42,))
    assert query.__getsql__() == ('UPDATE OR FAIL "tbl" SET "age"=?', (42,))
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        'mysql',
    ],
    indirect=True,
)
async def test_update_or_ignore(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update_or_ignore(tbl).set((tbl.age,), (42,))
    assert query.__getsql__() == ('UPDATE OR IGNORE "tbl" SET "age"=?', (42,))
    assert await txn.exq(query) == []


async def test_where(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update(tbl).set((tbl.age,), (42,)).where(tbl.name == 'foo')
    assert query.__getsql__() == (
        'UPDATE "tbl" SET "age"=? WHERE "tbl"."name" = ?',
        (42, 'foo'),
    )
    assert await txn.exq(query) == []


async def test_expr(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    query = Query().update(tbl).set((tbl.age,), (tbl.age + 1,)).where(tbl.name == 'foo')
    assert query.__getsql__() == (
        'UPDATE "tbl" SET "age"="tbl"."age" + ? WHERE "tbl"."name" = ?',
        (1, 'foo'),
    )
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
async def test_from(txn: Transaction) -> None:
    """Test update statement."""
    tbl = Table('tbl')
    dst = Table('dst')

    query = Query().update(tbl).set((tbl.age,), (dst.age,)).from_(dst)
    assert query.__getsql__() == ('UPDATE "tbl" SET "age"="dst"."age" FROM "dst"', ())
    assert await txn.exq(query) == []

    other_query = (
        Query().update(tbl).set((tbl.age,), (dst.age,)).from_(dst).where(tbl.name == dst.name)
    )
    assert other_query.__getsql__() == (
        'UPDATE "tbl" SET "age"="dst"."age" FROM "dst" WHERE "tbl"."name" = "dst"."name"',
        (),
    )
    assert await txn.exq(other_query) == []
