# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""ALTER TABLE tests."""

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
        Query().create_table(tbl).column('id', 'INTEGER').primary_key().column('num', 'INTEGER'),
    )


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='describe unimplemented')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='describe uninplemented')),
    ],
    indirect=True,
)
async def test_rename_to(txn: Transaction) -> None:
    """Test alter table statement."""
    tbl = Table('tbl')
    dst = Table('ref')

    assert await txn.exq(Query().alter_table(tbl).rename_to(dst)) == []
    assert await txn.exq(Query().pragma('table_info', value='ref')) == [
        (0, 'id', 'INTEGER', 0, None, 1),
        (1, 'num', 'INTEGER', 0, None, 0),
    ]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='describe unimplemented')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='describe uninplemented')),
    ],
    indirect=True,
)
async def test_rename_column(txn: Transaction) -> None:
    """Test alter table statement."""
    tbl = Table('tbl')
    assert await txn.exq(Query().alter_table(tbl).rename_column(tbl.id, tbl.tid)) == []
    assert await txn.exq(Query().pragma('table_info', value='tbl')) == [
        (0, 'tid', 'INTEGER', 0, None, 1),
        (1, 'num', 'INTEGER', 0, None, 0),
    ]


@pytest.mark.skipif('sys.version_info < (3, 9)')
@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='describe unimplemented')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='describe uninplemented')),
    ],
    indirect=True,
)
async def test_drop_column(txn: Transaction) -> None:
    """Test alter table statement."""
    tbl = Table('tbl')
    assert await txn.exq(Query().alter_table(tbl).drop_column(tbl.num)) == []
    assert await txn.exq(Query().pragma('table_info', value='tbl')) == [
        (0, 'id', 'INTEGER', 0, None, 1),
    ]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='describe unimplemented')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='describe uninplemented')),
    ],
    indirect=True,
)
async def test_add_column(txn: Transaction) -> None:
    """Test alter table statement."""
    tbl = Table('tbl')

    assert await txn.exq(Query().alter_table(tbl).add_column(tbl.name, 'TEXT')) == []
    assert await txn.exq(Query().pragma('table_info', value='tbl')) == [
        (0, 'id', 'INTEGER', 0, None, 1),
        (1, 'num', 'INTEGER', 0, None, 0),
        (2, 'name', 'TEXT', 0, None, 0),
    ]

    assert (
        await txn.exq(
            Query()
            .alter_table(tbl)
            .add_column(tbl.x1, 'INTEGER')
            .references(tbl, tbl.id)
            .on_update()
            .cascade()
            .deferrable()
            .default(1)
            .not_null()
            .on_conflict_ignore(),
        )
        == []
    )
    assert await txn.exq(Query().pragma('table_info', value='tbl')) == [
        (0, 'id', 'INTEGER', 0, None, 1),
        (1, 'num', 'INTEGER', 0, None, 0),
        (2, 'name', 'TEXT', 0, None, 0),
        (3, 'x1', 'INTEGER', 1, '1', 0),
    ]
