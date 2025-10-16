# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""PRAGMA tests."""

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
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_pragma(txn: Transaction) -> None:
    """Test pragma statement."""
    tbl = Table('foo')
    await txn.exq(Query().create_table(tbl).column('id', 'INTEGER'))

    query = Query().pragma('encoding')
    assert query.__getsql__() == ('PRAGMA "encoding"', ())
    assert await txn.exq(query) == [('UTF-8',)]

    query = Query().pragma('table_info', schema='main', value='foo')
    assert query.__getsql__() == ('PRAGMA "main"."table_info" = \'foo\'', ())
    assert await txn.exq(query) == [(0, 'id', 'INTEGER', 0, None, 0)]
