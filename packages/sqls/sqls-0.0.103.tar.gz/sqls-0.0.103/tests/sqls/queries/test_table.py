# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Table tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import Join, Query, Table
from sqls.queries.table import Tabular

if TYPE_CHECKING:
    from typing import TypeVar

    from sqls.interfaces import (
        Query as QueryProtocol,
        Transaction,
    )

    T = TypeVar('T')


async def test_table(txn: Transaction) -> None:
    """Test tables."""
    with pytest.raises(NotImplementedError):
        Tabular().__getsql__()

    tbl = Table('tbl', schema='foo')
    assert tbl.__getsql__()[0] == '"foo"."tbl"'
    assert tbl.as_('foo').__getsql__()[0] == '"foo"."tbl" AS "foo"'

    tbl = Table('tbl')
    assert tbl.__getsql__()[0] == '"tbl"'
    assert tbl.as_('foo').__getsql__()[0] == '"tbl" AS "foo"'

    assert tbl.bar.__getsql__() == ('"tbl"."bar"', ())
    assert (tbl / 'bar').__getsql__() == ('"tbl"."bar"', ())
    assert tbl.as_('foo').bar.__getsql__() == ('"foo"."bar"', ())
    assert (tbl.as_('foo') / 'bar').__getsql__() == ('"foo"."bar"', ())

    sub = Table('sub')

    assert Join().join(tbl).join(sub).__getsql__() == ('"tbl" JOIN "sub"', ())
    assert Join().join(tbl).join(sub).as_('foo').__getsql__() == ('("tbl" JOIN "sub") AS "foo"', ())

    async def exc(expr: QueryProtocol[T]) -> list[T]:
        return await txn.exq(expr)

    query = (
        Query()
        .with_(tbl, tbl.id, tbl.name)
        .as_(
            Query().values((1, 'foo'), (2, 'bar')),
        )
        .with_(sub, sub.id, sub.name)
        .as_(
            Query().values((1, 'baz'), (3, 'zar')),
        )
        .select(tbl.id.typed(int), tbl.name.typed(str), sub.id.typed(int), sub.name.typed(str))
        .from_(Join().join(tbl).join(sub, typ='cross'))
    )
    assert sorted(await exc(query)) == [
        (1, 'foo', 1, 'baz'),
        (1, 'foo', 3, 'zar'),
        (2, 'bar', 1, 'baz'),
        (2, 'bar', 3, 'zar'),
    ]

    alias = Table('alias')

    query = (
        Query()
        .with_(tbl, tbl.id, tbl.name)
        .as_(
            Query().values((1, 'foo'), (2, 'bar')),
        )
        .with_(sub, sub.id, sub.name)
        .as_(
            Query().values((1, 'baz'), (3, 'zar')),
        )
        .select(alias.id.typed(int), alias.name.typed(str), sub.id.typed(int), sub.name.typed(str))
        .from_(
            Join()
            .join(tbl.as_('alias'))
            .join(tbl, typ='cross')
            .join(sub)
            .on_(alias.id == sub.id)
            .join(sub.as_('other'), typ='cross'),
        )
    )
    assert await exc(query) == [
        (1, 'foo', 1, 'baz'),
        (1, 'foo', 1, 'baz'),
        (1, 'foo', 1, 'baz'),
        (1, 'foo', 1, 'baz'),
    ]
