# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""WINDOW tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprLiteral, Query, Table, Window

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
        .column('char', 'TEXT')
        .unique()
        .column('name', 'TEXT'),
    )

    await txn.exq(
        Query()
        .insert(tbl)
        .columns(tbl.char, tbl.name)
        .values(
            ('A', 'one'),
            ('B', 'two'),
            ('C', 'three'),
            ('D', 'one'),
            ('E', 'two'),
            ('F', 'three'),
            ('G', 'one'),
        ),
    )


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',  # does not use txn
    ],
    indirect=True,
)
def test_syntax() -> None:
    """Test syntax."""
    tbl = Table('tbl')
    assert (Window().execute('lead', tbl.id).over_name('window_name').__getsql__())[0] == (
        'lead("tbl"."id") OVER window_name'
    )

    assert (
        Window()
        .execute('lead', tbl.id)
        .filter(tbl.name == 'one')
        .over_name('window_name')
        .__getsql__()
    )[0] == ('lead("tbl"."id") FILTER (WHERE "tbl"."name" = ?) OVER window_name')

    assert (Window().execute('lead', tbl.id).over_definition().__getsql__())[0] == (
        'lead("tbl"."id") OVER ()'
    )

    assert (
        Window().execute('lead', tbl.id).over_definition().base_window('window_name').__getsql__()
    )[0] == ('lead("tbl"."id") OVER (window_name)')

    assert (
        Window().execute('lead', tbl.id).over_definition().partition_by(tbl.rel_id).__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( PARTITION BY "tbl"."rel_id")')

    assert (Window().execute('lead', tbl.id).over_definition().order_by(tbl.a, tbl.b).__getsql__())[
        0
    ] == ('lead("tbl"."id") OVER ( ORDER BY "tbl"."a", "tbl"."b")')

    assert (Window().execute('lead', tbl.id).over_definition().range().precedeing().__getsql__())[
        0
    ] == ('lead("tbl"."id") OVER ( RANGE UNBOUNDED PRECEDING)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .rows()
        .precedeing(ExprLiteral(1))
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( ROWS ? PRECEDING)')

    assert (Window().execute('lead', tbl.id).over_definition().groups().current_row().__getsql__())[
        0
    ] == ('lead("tbl"."id") OVER ( GROUPS CURRENT ROW)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .between()
        .precedeing()
        .following(ExprLiteral(1))
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS BETWEEN UNBOUNDED PRECEDING AND ? FOLLOWING)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .between()
        .precedeing(ExprLiteral(1))
        .following()
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS BETWEEN ? PRECEDING AND UNBOUNDED FOLLOWING)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .between()
        .current_row()
        .precedeing(ExprLiteral(1))
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS BETWEEN CURRENT ROW AND ? PRECEDING)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .between()
        .following(ExprLiteral(1))
        .current_row()
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS BETWEEN ? FOLLOWING AND CURRENT ROW)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .precedeing()
        .exclude_no_others()
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS UNBOUNDED PRECEDING EXCLUDE NO OTHERS)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .precedeing()
        .exclude_current_row()
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS UNBOUNDED PRECEDING EXCLUDE CURRENT ROW)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .precedeing()
        .exclude_group()
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS UNBOUNDED PRECEDING EXCLUDE GROUP)')

    assert (
        Window()
        .execute('lead', tbl.id)
        .over_definition()
        .groups()
        .precedeing()
        .exclude_ties()
        .__getsql__()
    )[0] == ('lead("tbl"."id") OVER ( GROUPS UNBOUNDED PRECEDING EXCLUDE TIES)')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='group_concat unsupported')),
    ],
    indirect=True,
)
async def test_filter(txn: Transaction) -> None:
    """Test filter."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(
            tbl.name.typed(str),
            tbl.id.typed(int),
            tbl.char.typed(str),
            Window()
            .execute('group_concat', tbl.char, ExprLiteral('.'))
            .filter(tbl.name != 'two')
            .over_definition()
            .order_by(tbl.id)
            .typed(str),
        )
        .from_(tbl)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name", "tbl"."id", "tbl"."char", '
        'group_concat("tbl"."char", ?) FILTER (WHERE "tbl"."name" != ?) '
        'OVER ( ORDER BY "tbl"."id") FROM "tbl"',
        ('.', 'two'),
    )
    assert await txn.exq(query) == [
        ('one', 1, 'A', 'A'),
        ('two', 2, 'B', 'A'),
        ('three', 3, 'C', 'A.C'),
        ('one', 4, 'D', 'A.C.D'),
        ('two', 5, 'E', 'A.C.D'),
        ('three', 6, 'F', 'A.C.D.F'),
        ('one', 7, 'G', 'A.C.D.F.G'),
    ]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='group_concat unsupported')),
    ],
    indirect=True,
)
async def test_aggregate(txn: Transaction) -> None:
    """Test aggregate."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(
            tbl.id.typed(int),
            tbl.char.typed(str),
            Window()
            .execute('group_concat', tbl.char, ExprLiteral('.'))
            .over_definition()
            .order_by(tbl.id)
            .rows()
            .between()
            .precedeing(ExprLiteral(1))
            .following(ExprLiteral(1))
            .typed(str),
        )
        .from_(tbl)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."id", "tbl"."char", '
        'group_concat("tbl"."char", ?) OVER ( ORDER BY "tbl"."id" ROWS BETWEEN '
        '? PRECEDING AND ? FOLLOWING) FROM "tbl"',
        ('.', 1, 1),
    )
    assert await txn.exq(query) == [
        (1, 'A', 'A.B'),
        (2, 'B', 'A.B.C'),
        (3, 'C', 'B.C.D'),
        (4, 'D', 'C.D.E'),
        (5, 'E', 'D.E.F'),
        (6, 'F', 'E.F.G'),
        (7, 'G', 'F.G'),
    ]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='group_concat unsupported')),
    ],
    indirect=True,
)
async def test_partition(txn: Transaction) -> None:
    """Test partition by."""
    tbl = Table('tbl')
    query = (
        Query()
        .select(
            tbl.name.typed(str),
            tbl.id.typed(int),
            tbl.char.typed(str),
            Window()
            .execute('group_concat', tbl.char, ExprLiteral('.'))
            .over_definition()
            .partition_by(tbl.name)
            .order_by(tbl.id)
            .rows()
            .between()
            .current_row()
            .following()
            .typed(str),
        )
        .from_(tbl)
    )
    assert query.__getsql__() == (
        'SELECT "tbl"."name", "tbl"."id", "tbl"."char", '
        'group_concat("tbl"."char", ?) OVER ( PARTITION BY "tbl"."name" ORDER BY "tbl"."id" ROWS '
        'BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) FROM "tbl"',
        ('.',),
    )
    assert await txn.exq(query) == [
        ('one', 1, 'A', 'A.D.G'),
        ('one', 4, 'D', 'D.G'),
        ('one', 7, 'G', 'G'),
        ('three', 3, 'C', 'C.F'),
        ('three', 6, 'F', 'F'),
        ('two', 2, 'B', 'B.E'),
        ('two', 5, 'E', 'E'),
    ]

    query_ordered = (
        Query()
        .select(
            tbl.name.typed(str),
            tbl.id.typed(int),
            tbl.char.typed(str),
            Window()
            .execute('group_concat', tbl.char, ExprLiteral('.'))
            .over_definition()
            .partition_by(tbl.name)
            .order_by(tbl.id)
            .rows()
            .between()
            .current_row()
            .following()
            .typed(str),
        )
        .from_(tbl)
        .order_by(tbl.id)
    )
    assert query_ordered.__getsql__() == (
        'SELECT "tbl"."name", "tbl"."id", "tbl"."char", '
        'group_concat("tbl"."char", ?) OVER ( PARTITION BY "tbl"."name" ORDER BY "tbl"."id" ROWS '
        'BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) FROM "tbl" ORDER BY "tbl"."id"',
        ('.',),
    )
    assert await txn.exq(query_ordered) == [
        ('one', 1, 'A', 'A.D.G'),
        ('two', 2, 'B', 'B.E'),
        ('three', 3, 'C', 'C.F'),
        ('one', 4, 'D', 'D.G'),
        ('two', 5, 'E', 'E'),
        ('three', 6, 'F', 'F'),
        ('one', 7, 'G', 'G'),
    ]
