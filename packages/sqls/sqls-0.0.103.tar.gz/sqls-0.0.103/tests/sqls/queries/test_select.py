# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SELECT tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprFunction, ExprLiteral, Query, QueryError, Table

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


async def test_values(txn: Transaction) -> None:
    """Test select statement."""
    with pytest.raises(QueryError, match='one row'):
        Query().values().__getsql__()

    with pytest.raises(QueryError, match='one column'):
        Query().values(()).__getsql__()

    query = Query().values((1, 2), (3, 4))
    assert query.__getsql__() == ('VALUES(?, ?),(?, ?)', (1, 2, 3, 4))
    assert await txn.exq(query) == [(1, 2), (3, 4)]


async def test_from_table(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = Query().select(tbl.id.typed(int)).from_(tbl)
    assert query.__getsql__() == ('SELECT "tbl"."id" FROM "tbl"', ())
    assert await txn.exq(query) == [(1,), (2,), (3,), (4,)]


async def test_from_subquery(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(Table('').__star__.typed(object))
        .from_(
            Query().select(tbl.id.typed(int)).from_(tbl).table().as_('sub'),
        )
    )
    assert query.__getsql__() == ('SELECT * FROM (SELECT "tbl"."id" FROM "tbl") AS "sub"', ())
    assert await txn.exq(query) == [(1,), (2,), (3,), (4,)]


async def test_where(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = Query().select(tbl.id.typed(int)).from_(tbl).where(None)
    assert query.__getsql__() == ('SELECT "tbl"."id" FROM "tbl"', ())
    assert await txn.exq(query) == [(1,), (2,), (3,), (4,)]

    query = Query().select(tbl.id.typed(int)).from_(tbl).where(tbl.name == 'Ringo')
    assert query.__getsql__() == ('SELECT "tbl"."id" FROM "tbl" WHERE "tbl"."name" = ?', ('Ringo',))
    assert await txn.exq(query) == [(3,)]


async def test_function(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query().select(ExprFunction('COUNT', tbl.id).typed(int)).from_(tbl).group_by(tbl.age > 44)
    )
    assert query.__getsql__() == (
        'SELECT COUNT("tbl"."id") FROM "tbl" GROUP BY "tbl"."age" > ?',
        (44,),
    )
    assert await txn.exq(query) == [(3,), (1,)]


async def test_groupby(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(
            ExprFunction('LENGTH', tbl.name).typed(int),
            ExprFunction('COUNT', tbl.id).typed(int),
        )
        .from_(tbl)
        .group_by(ExprFunction('LENGTH', tbl.name))
        .having(ExprFunction('COUNT', tbl.id) > 1)
    )
    assert query.__getsql__() == (
        'SELECT LENGTH("tbl"."name"), COUNT("tbl"."id") FROM "tbl" GROUP BY '
        'LENGTH("tbl"."name") HAVING (COUNT("tbl"."id")) > ?',
        (1,),
    )
    assert await txn.exq(query) == [(4, 2)]


async def test_union(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age >= 43)
        .union()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age < 45)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" >= ? UNION '
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" < ?',
        (43, 45),
    )
    assert sorted(await txn.exq(query)) == [
        ('George',),
        ('John',),
        ('Paul',),
        ('Ringo',),
    ]


async def test_union_query(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age >= 43)
        .union_query(
            Query().select(tbl.name.typed(str)).from_(tbl).where(tbl.age < 45),
        )
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" >= ? UNION '
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" < ?',
        (43, 45),
    )
    assert sorted(await txn.exq(query)) == [
        ('George',),
        ('John',),
        ('Paul',),
        ('Ringo',),
    ]


async def test_union_all(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age >= 43)
        .union_all()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age < 45)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" >= ? UNION ALL '
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" < ?',
        (43, 45),
    )
    assert await txn.exq(query) == [
        ('Paul',),
        ('Ringo',),
        ('George',),
        ('John',),
        ('Paul',),
        ('Ringo',),
    ]


async def test_intersect(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age >= 43)
        .intersect()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age < 45)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" >= ? INTERSECT '
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" < ?',
        (43, 45),
    )
    assert sorted(await txn.exq(query)) == [
        ('Paul',),
        ('Ringo',),
    ]


async def test_except(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age >= 43)
        .except_()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .where(tbl.age < 45)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" >= ? EXCEPT '
        'SELECT "tbl"."name" FROM "tbl" WHERE "tbl"."age" < ?',
        (43, 45),
    )
    assert sorted(await txn.exq(query)) == [
        ('George',),
    ]


async def test_orderby(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = Query().select(tbl.name.typed(str)).from_(tbl).order_by(tbl.name)
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" ORDER BY "tbl"."name"',
        (),
    )
    assert await txn.exq(query) == [
        ('George',),
        ('John',),
        ('Paul',),
        ('Ringo',),
    ]

    query = Query().select(tbl.name.typed(str)).from_(tbl).order_by(tbl.name, desc=True)
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" ORDER BY "tbl"."name" DESC',
        (),
    )
    assert await txn.exq(query) == [
        ('Ringo',),
        ('Paul',),
        ('John',),
        ('George',),
    ]


async def test_limit(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = Query().select(tbl.name.typed(str)).from_(tbl).order_by(tbl.name).limit(1).offset(1)
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" ORDER BY "tbl"."name" LIMIT ? OFFSET ?',
        (1, 1),
    )
    assert await txn.exq(query) == [
        ('John',),
    ]

    query = Query().select(tbl.name.typed(str)).from_(tbl).order_by(tbl.name).limit(2).offset(2)
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" ORDER BY "tbl"."name" LIMIT ? OFFSET ?',
        (2, 2),
    )
    assert await txn.exq(query) == [
        ('Paul',),
        ('Ringo',),
    ]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_limit_expr(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(tbl.name.typed(str))
        .from_(tbl)
        .order_by(tbl.name)
        .limit(ExprLiteral(1) + 1)
        .offset(ExprLiteral(1) + 1)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name" FROM "tbl" ORDER BY "tbl"."name" LIMIT ? + ? OFFSET ? + ?',
        (1, 1, 1, 1),
    )
    assert await txn.exq(query) == [
        ('Paul',),
        ('Ringo',),
    ]


async def test_with(txn: Transaction) -> None:
    """Test select statement."""
    tbl = Table('tbl')
    dst = Table('dst')
    query = (
        Query()
        .with_(tbl, tbl.id, tbl.id2)
        .as_(
            Query().values((1, 2)),
        )
        .with_(dst, dst.id, dst.id2)
        .as_(
            Query().values((3, 4)),
        )
        .select(tbl.__star__.typed(object))
        .from_(tbl)
        .union()
        .select(dst.__star__.typed(object))
        .from_(dst)
    )
    assert query.__getsql__() == (
        'WITH "tbl" (id, id2) AS (VALUES(?, ?)), "dst" (id, id2) AS (VALUES(?, ?)) '
        'SELECT "tbl".* FROM "tbl" UNION SELECT "dst".* FROM "dst"',
        (1, 2, 3, 4),
    )
    assert await txn.exq(query) == [(1, 2), (3, 4)]  # type: ignore[comparison-overlap]
