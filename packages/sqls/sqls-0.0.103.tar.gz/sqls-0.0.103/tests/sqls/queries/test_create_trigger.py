# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""CREATE TRIGGER tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprLiteral, Query, Table

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
        .column('other', 'TEXT'),
    )

    dst = Table('dst')
    await txn.exq(
        Query()
        .create_table(dst)
        .column('id', 'INTEGER')
        .primary_key()
        .column('cause', 'TEXT')
        .column('columns', 'TEXT'),
    )

    view = Table('view')
    await txn.exq(
        Query().create_view(view).as_(Query().select(tbl.__star__.typed(object)).from_(tbl)),
    )


async def get_lastentry(txn: Transaction) -> tuple[int, str, str]:
    """Get last entry from dst."""
    dst = Table('dst')
    return (
        await txn.exq(
            Query()
            .select(dst.id.typed(int), dst.cause.typed(str), dst.columns.typed(str))
            .from_(dst)
            .order_by(dst.id, desc=True)
            .limit(1),
        )
    )[0]


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_after_insert(txn: Transaction) -> None:
    """Test create trigger statement."""
    tbl = Table('tbl')
    dst = Table('dst')

    new = Table('NEW')
    assert (
        await txn.exq(
            Query()
            .create_trigger(Table('after_insert'))
            .after()
            .insert()
            .on_(tbl)
            .for_each_row()
            .when(new.name != ExprLiteral('ignored', bind=False))
            .statements(
                Query()
                .insert(dst)
                .columns(dst.cause, dst.columns)
                .values(ExprLiteral(('tbl_insert', new.name), bind=False)),
            ),
        )
        == []
    )

    assert await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',))) == []
    assert await get_lastentry(txn) == (1, 'tbl_insert', 'foo')
    assert await txn.exq(Query().insert(tbl).columns(tbl.name).values(('ignored',))) == []
    assert await get_lastentry(txn) == (1, 'tbl_insert', 'foo')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_before_update(txn: Transaction) -> None:
    """Test create trigger statement."""
    tbl = Table('tbl')
    dst = Table('dst')

    old = Table('OLD')
    new = Table('NEW')
    assert (
        await txn.exq(
            Query()
            .create_trigger(Table('before_update'))
            .before()
            .update()
            .on_(tbl)
            .for_each_row()
            .when(new.name != old.name)
            .statements(
                Query()
                .insert(dst)
                .columns(dst.cause, dst.columns)
                .values(
                    (
                        ExprLiteral('tbl_update', bind=False),
                        old.name.strconcat(ExprLiteral('->', bind=False)).strconcat(new.name),
                    ),
                ),
            ),
        )
        == []
    )
    await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',)))
    await txn.exq(Query().update(tbl).set((tbl.name,), ('bar',)).where(tbl.name == 'foo'))
    assert await get_lastentry(txn) == (1, 'tbl_update', 'foo->bar')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_before_update_of(txn: Transaction) -> None:
    """Test create trigger statement."""
    tbl = Table('tbl')
    dst = Table('dst')

    new = Table('NEW')
    assert (
        await txn.exq(
            Query()
            .create_trigger(Table('before_update_of'))
            .before()
            .update(of_=[tbl.other])
            .on_(tbl)
            .for_each_row()
            .statements(
                Query()
                .insert(dst)
                .columns(dst.cause, dst.columns)
                .values(
                    (
                        ExprLiteral('tbl_update_other', bind=False),
                        ExprLiteral('->', bind=False).strconcat(new.other),
                    ),
                ),
            ),
        )
        == []
    )
    await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',)))
    await txn.exq(Query().update(tbl).set((tbl.other,), ('bar',)).where(tbl.name == 'foo'))
    assert await get_lastentry(txn) == (1, 'tbl_update_other', '->bar')
    await txn.exq(Query().update(tbl).set((tbl.name,), ('bar',)).where(tbl.name == 'foo'))
    assert await get_lastentry(txn) == (1, 'tbl_update_other', '->bar')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_delete(txn: Transaction) -> None:
    """Test create trigger statement."""
    tbl = Table('tbl')
    dst = Table('dst')

    old = Table('OLD')
    assert (
        await txn.exq(
            Query()
            .create_trigger(Table('delete'))
            .delete()
            .on_(tbl)
            .statements(
                Query()
                .insert(dst)
                .columns(dst.cause, dst.columns)
                .values((ExprLiteral('tbl_delete', bind=False), old.name)),
            ),
        )
        == []
    )
    await txn.exq(Query().insert(tbl).columns(tbl.name).values(('foo',)))
    await txn.exq(Query().delete(tbl).where(tbl.name == 'foo'))
    assert await get_lastentry(txn) == (1, 'tbl_delete', 'foo')


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='other syntax')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='other syntax')),
    ],
    indirect=True,
)
async def test_instead_of(txn: Transaction) -> None:
    """Test create trigger statement."""
    dst = Table('dst')
    view = Table('view')

    new = Table('NEW')
    assert (
        await txn.exq(
            Query()
            .create_trigger(Table('instead_of'))
            .instead_of()
            .insert()
            .on_(view)
            .statements(
                Query()
                .insert(dst)
                .columns(dst.cause, dst.columns)
                .values(
                    (
                        ExprLiteral('instead_of', bind=False),
                        new.name.strconcat(ExprLiteral(' ', bind=False).strconcat(new.other)),
                    ),
                ),
            ),
        )
        == []
    )
    await txn.exq(Query().insert(view).columns(view.name, view.other).values(('vname', 'vother')))
    assert await get_lastentry(txn) == (1, 'instead_of', 'vname vother')
