# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""DELETE FROM tests."""

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
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('name', 'TEXT')
        .unique()
        .column('age', 'INTEGER'),
    )


async def test_delete(txn: Transaction) -> None:
    """Test delete statement."""
    tbl = Table('tbl')
    delete = Query().delete(tbl)
    assert delete.__getsql__() == ('DELETE FROM "tbl"', ())
    await txn.exq(delete)

    delete_where = Query().delete(tbl).where(tbl.name == 'foo')
    assert delete_where.__getsql__() == ('DELETE FROM "tbl" WHERE "tbl"."name" = ?', ('foo',))
    await txn.exq(delete_where)
