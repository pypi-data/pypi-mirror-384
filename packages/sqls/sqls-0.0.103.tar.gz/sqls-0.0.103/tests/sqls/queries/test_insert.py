# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""INSERT tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprLiteral, Query, QueryError, Table

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.fixture(autouse=True)
async def _autotable(txn: Transaction) -> None:
    tbl = Table('tbl')
    await txn.exq(
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('name', 'TEXT')
        .unique()
        .column('age', 'INTEGER'),
    )


async def test_default_values(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    query = Query().insert(tbl).default_values()
    assert query.__getsql__()[0] == 'INSERT INTO "tbl" DEFAULT VALUES'
    assert await txn.exq(query) == []


async def test_insert_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    with pytest.raises(QueryError, match='one row'):
        Query().insert(tbl).columns(tbl.name, tbl.age).values().__getsql__()

    with pytest.raises(QueryError, match='one column'):
        Query().insert(tbl).columns(tbl.name, tbl.age).values(()).__getsql__()

    query = Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42))
    assert query.__getsql__() == ('INSERT INTO "tbl" ("name", "age") VALUES(?, ?)', ('Ringo', 42))
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
async def test_replace_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = Query().replace(tbl).columns(tbl.name, tbl.age).values(('Ringo', 43))
    assert query.__getsql__() == ('REPLACE INTO "tbl" ("name", "age") VALUES(?, ?)', ('Ringo', 43))
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
async def test_insert_or_replace_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = Query().insert_or_replace(tbl).columns(tbl.name, tbl.age).values(('Ringo', 43))
    assert query.__getsql__() == (
        'INSERT OR REPLACE INTO "tbl" ("name", "age") VALUES(?, ?)',
        ('Ringo', 43),
    )
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
async def test_insert_or_rollback_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = Query().insert_or_rollback(tbl).columns(tbl.name, tbl.age).values(('Ringo', 43))
    assert query.__getsql__() == (
        'INSERT OR ROLLBACK INTO "tbl" ("name", "age") VALUES(?, ?)',
        ('Ringo', 43),
    )
    with pytest.raises(Exception, match='UNIQUE constraint failed'):
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
async def test_insert_or_abort_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = Query().insert_or_abort(tbl).columns(tbl.name, tbl.age).values(('Ringo', 43))
    assert query.__getsql__() == (
        'INSERT OR ABORT INTO "tbl" ("name", "age") VALUES(?, ?)',
        ('Ringo', 43),
    )
    with pytest.raises(Exception, match='UNIQUE constraint failed'):
        await txn.exq(query)


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_insert_or_fail_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = Query().insert_or_fail(tbl).columns(tbl.name, tbl.age).values(('Ringo', 43))
    assert query.__getsql__() == (
        'INSERT OR FAIL INTO "tbl" ("name", "age") VALUES(?, ?)',
        ('Ringo', 43),
    )
    with pytest.raises(Exception, match='UNIQUE constraint failed'):
        await txn.exq(query)


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        'mysql',
    ],
    indirect=True,
)
async def test_insert_or_ignore_into(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = Query().insert_or_ignore(tbl).columns(tbl.name, tbl.age).values(('Ringo', 43))
    assert query.__getsql__() == (
        'INSERT OR IGNORE INTO "tbl" ("name", "age") VALUES(?, ?)',
        ('Ringo', 43),
    )
    assert await txn.exq(query) == []


async def test_insert_from_select(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .insert(tbl)
        .columns(tbl.name, tbl.age)
        .select(
            Query().select(
                ExprLiteral('George').typed(str),
                ExprLiteral(42).typed(int),
            ),
        )
    )
    assert query.__getsql__() == ('INSERT INTO "tbl" ("name", "age") SELECT ?, ?', ('George', 42))
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
async def test_insert_on_conflict_do_nothing(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    query = (
        Query()
        .insert(tbl)
        .columns(tbl.name, tbl.age)
        .values(('Ringo', 43))
        .on_conflict_do_nothing()
    )
    assert query.__getsql__() == (
        'INSERT INTO "tbl" ("name", "age") VALUES(?, ?) ON CONFLICT DO NOTHING',
        ('Ringo', 43),
    )
    assert await txn.exq(query) == []
    assert await txn.exq(Query().select(tbl.age.typed(int)).from_(tbl)) == [(42,)]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_insert_on_conflict_update_set(txn: Transaction) -> None:
    """Test insert statement."""
    tbl = Table('tbl')
    excluded = Table('excluded')
    await txn.exq(Query().insert(tbl).columns(tbl.name, tbl.age).values(('Ringo', 42)))

    with pytest.raises(QueryError, match='same length'):
        (
            Query()
            .insert(tbl)
            .columns(tbl.name, tbl.age)
            .values(('Ringo', 40))
            .on_conflict(tbl.name)
            .update_set((tbl.name, tbl.age), (excluded.age,))
            .where(excluded.age > tbl.age)
            .__getsql__()
        )

    query = (
        Query()
        .insert(tbl)
        .columns(tbl.name, tbl.age)
        .values(('Ringo', 40))
        .on_conflict(tbl.name)
        .update_set((tbl.age,), (excluded.age,))
        .where(excluded.age > tbl.age)
    )
    assert query.__getsql__() == (
        'INSERT INTO "tbl" ("name", "age") VALUES(?, ?) ON CONFLICT ("tbl"."name") DO '
        'UPDATE SET age = "excluded"."age" WHERE "excluded"."age" > "tbl"."age"',
        ('Ringo', 40),
    )
    assert await txn.exq(query) == []
    assert await txn.exq(Query().select(tbl.age.typed(int)).from_(tbl)) == [(42,)]

    query = (
        Query()
        .insert(tbl)
        .columns(tbl.name, tbl.age)
        .values(('Ringo', 43))
        .on_conflict(tbl.name)
        .update_set((tbl.age,), (excluded.age,))
        .where(excluded.age > tbl.age)
    )
    assert query.__getsql__() == (
        'INSERT INTO "tbl" ("name", "age") VALUES(?, ?) ON CONFLICT ("tbl"."name") DO '
        'UPDATE SET age = "excluded"."age" WHERE "excluded"."age" > "tbl"."age"',
        ('Ringo', 43),
    )
    assert await txn.exq(query) == []
    assert await txn.exq(Query().select(tbl.age.typed(int)).from_(tbl)) == [(43,)]

    query = (
        Query()
        .insert(tbl)
        .columns(tbl.name, tbl.age)
        .values(('Ringo', 44))
        .on_conflict(tbl.name)
        .update_set((tbl.age,), (0,))
        .where(excluded.age > tbl.age)
    )
    assert query.__getsql__() == (
        'INSERT INTO "tbl" ("name", "age") VALUES(?, ?) ON CONFLICT ("tbl"."name") DO '
        'UPDATE SET age = ? WHERE "excluded"."age" > "tbl"."age"',
        ('Ringo', 44, 0),
    )
    assert await txn.exq(query) == []
    assert await txn.exq(Query().select(tbl.age.typed(int)).from_(tbl)) == [(0,)]
