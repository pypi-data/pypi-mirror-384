# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""EXPLAIN tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import Explain, Query, Table

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='no vaccum')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='no vacuum')),
    ],
    indirect=True,
)
async def test_vacuum(txn: Transaction) -> None:
    """Test explain statement."""
    query = Explain().vacuum()
    assert query.__getsql__() == ('EXPLAIN VACUUM', ())
    assert (
        [
            x[1]  # type: ignore[misc]
            for x in await txn.exq(query)
        ][:3]
        == ['Init', 'Vacuum', 'Halt']
    )  # PY3.8: no 'Goto'


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='no query plan')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='no query plan')),
    ],
    indirect=True,
)
async def test_query_plan(txn: Transaction) -> None:
    """Test explain statement."""
    tbl = Table('tbl')
    await txn.exq(Query().create_table(tbl).column('id', 'INTEGER'))

    query = Explain(query_plan=True).select(tbl.id.typed(int)).from_(tbl)
    assert query.__getsql__() == ('EXPLAIN QUERY PLAN SELECT "tbl"."id" FROM "tbl"', ())
    assert await txn.exq(
        query,
    ) in (  # type: ignore[comparison-overlap]
        [(2, 0, 0, 'SCAN tbl')],
        [(2, 0, 216, 'SCAN tbl')],  # PY3.12
    )


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        'mysql',
    ],
    indirect=True,
)
async def test_query(txn: Transaction) -> None:
    """Test explain statement."""
    tbl = Table('tbl')
    await txn.exq(Query().create_table(tbl).column('id', 'INTEGER'))

    query = Explain().select(tbl.id.typed(object)).from_(tbl)
    assert query.__getsql__() == ('EXPLAIN SELECT "tbl"."id" FROM "tbl"', ())
    assert await txn.exq(query) in (
        [
            (0, 'Init', 0, 7, 0, None, 0, None),
            (1, 'OpenRead', 0, 2, 0, '1', 0, None),
            (2, 'Rewind', 0, 6, 0, None, 0, None),
            (3, 'Column', 0, 0, 1, None, 0, None),
            (4, 'ResultRow', 1, 1, 0, None, 0, None),
            (5, 'Next', 0, 3, 0, None, 1, None),
            (6, 'Halt', 0, 0, 0, None, 0, None),
            (7, 'Transaction', 0, 0, 1, '0', 1, None),
            (8, 'Goto', 0, 1, 0, None, 0, None),
        ],
        [('Seq Scan on tbl  (cost=0.00..35.50 rows=2550 width=4)',)],
        [(1, 'SIMPLE', 'tbl', 'ALL', None, None, None, None, '1', '')],
    )
