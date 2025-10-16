# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Squal tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import Query, Table

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_analyze(txn: Transaction) -> None:
    """Test analyze statement."""
    tbl = Table('tbl')
    await txn.exq(Query().create_table(tbl).column('id', 'INTEGER'))

    query = Query().analyze()
    assert query.__getsql__() == ('ANALYZE', ())
    assert await txn.exq(query) == []

    query = Query().analyze(tbl)
    assert query.__getsql__() == ('ANALYZE "tbl"', ())
    assert await txn.exq(query) == []

    query = Query().analyze('tbl')
    assert query.__getsql__() == ('ANALYZE "tbl"', ())
    assert await txn.exq(query) == []
