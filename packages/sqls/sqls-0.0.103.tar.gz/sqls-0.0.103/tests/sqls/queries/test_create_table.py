# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""CREATE TABLE tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprLiteral, Query, Table
from sqls.transactions.mysql import Transaction as Mysql
from sqls.transactions.postgresql import Transaction as Postgres
from sqls.transactions.sqlite import Transaction as Sqlite

if TYPE_CHECKING:
    from sqls.interfaces import Transaction


async def test_single_column(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER')
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER)'
    assert await txn.exq(query) == []


async def test_primary_key(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').primary_key()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER PRIMARY KEY)'
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
async def test_primary_key_autoincrement(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').primary_key(autoincrement=True)
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER PRIMARY KEY AUTOINCREMENT)'
    assert await txn.exq(query) == []


async def test_not_null(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').not_null()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER NOT NULL)'
    assert await txn.exq(query) == []


async def test_unique(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').unique()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER UNIQUE)'
    assert await txn.exq(query) == []


async def test_check(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .check(tbl.id > ExprLiteral(42, bind=False))
    )
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER CHECK ("tbl"."id" > 42))'
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
async def test_rollback(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').unique().on_conflict_rollback()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER UNIQUE ON CONFLICT ROLLBACK)'
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
async def test_abort(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').unique().on_conflict_abort()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER UNIQUE ON CONFLICT ABORT)'
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
async def test_fail(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').unique().on_conflict_fail()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER UNIQUE ON CONFLICT FAIL)'
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
async def test_ignore(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').unique().on_conflict_ignore()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER UNIQUE ON CONFLICT IGNORE)'
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
async def test_replace(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').unique().on_conflict_replace()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER UNIQUE ON CONFLICT REPLACE)'
    assert await txn.exq(query) == []


async def test_default(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('age', 'INTEGER').default(42)
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("age" INTEGER DEFAULT 42)'
    assert await txn.exq(query) == []


async def test_default_text(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('name', 'TEXT').default('foo')
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("name" TEXT DEFAULT \'foo\')'
    assert await txn.exq(query) == []


async def test_default_null(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('age', 'INTEGER').default(None)
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("age" INTEGER DEFAULT NULL)'
    assert await txn.exq(query) == []


async def test_default_true(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('age', 'INTEGER').default(True)
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("age" INTEGER DEFAULT TRUE)'
    assert await txn.exq(query) == []


async def test_default_false(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('age', 'INTEGER').default(False)
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("age" INTEGER DEFAULT FALSE)'
    assert await txn.exq(query) == []


async def test_collate(txn: Transaction) -> None:
    """Test create table statement."""
    collation = {
        Sqlite: 'NOCASE',
        Postgres: '"en_US"',
        Mysql: 'utf8_general_ci',
    }[type(txn)]
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'TEXT').collate(collation)
    assert query.__getsql__()[0] == f'CREATE TABLE "tbl" ("id" TEXT COLLATE {collation})'
    assert await txn.exq(query) == []


async def test_references(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('lid', 'INTEGER')
        .references(tbl, tbl.id)
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" ("id" INTEGER PRIMARY KEY, "lid" INTEGER REFERENCES "tbl" ("id"))'
    )
    assert await txn.exq(query) == []


async def test_action_set_null_set_default(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('lid', 'INTEGER')
        .references(tbl, tbl.id)
        .on_delete()
        .set_null()
        .on_update()
        .set_default()
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER PRIMARY KEY, "lid" INTEGER REFERENCES "tbl" ("id")'
        ' ON DELETE SET NULL'
        ' ON UPDATE SET DEFAULT'
        ')'
    )
    assert await txn.exq(query) == []


async def test_action_cascade_restrict(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('lid', 'INTEGER')
        .references(tbl, tbl.id)
        .on_delete()
        .cascade()
        .on_update()
        .restrict()
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER PRIMARY KEY, "lid" INTEGER REFERENCES "tbl" ("id")'
        ' ON DELETE CASCADE'
        ' ON UPDATE RESTRICT'
        ')'
    )
    assert await txn.exq(query) == []


async def test_no_action(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('lid', 'INTEGER')
        .references(tbl, tbl.id)
        .on_delete()
        .no_action()
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER PRIMARY KEY, "lid" INTEGER REFERENCES "tbl" ("id")'
        ' ON DELETE NO ACTION'
        ')'
    )
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
async def test_deferrable(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('lid', 'INTEGER')
        .references(tbl, tbl.id)
        .deferrable()
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER PRIMARY KEY, "lid" INTEGER REFERENCES "tbl" ("id")'
        ' DEFERRABLE'
        ')'
    )
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
async def test_not_deferrable(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .primary_key()
        .column('lid', 'INTEGER')
        .references(tbl, tbl.id)
        .deferrable(is_deferrable=False)
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER PRIMARY KEY, "lid" INTEGER REFERENCES "tbl" ("id")'
        ' NOT DEFERRABLE'
        ')'
    )
    assert await txn.exq(query) == []


async def test_generated(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    anon = Table('')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .column('lid', 'INTEGER')
        .generated(anon.id + ExprLiteral(1, bind=False))
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" ("id" INTEGER, "lid" INTEGER GENERATED ALWAYS AS ("id" + 1) VIRTUAL)'
    )
    assert await txn.exq(query) == []


async def test_unique_columns(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .column('lid', 'INTEGER')
        .unique_columns('id', 'lid')
    )
    assert (
        query.__getsql__()[0]
        == 'CREATE TABLE "tbl" ("id" INTEGER, "lid" INTEGER, UNIQUE (id, lid))'
    )
    assert await txn.exq(query) == []


async def test_check_columns(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .check_columns(tbl.id > ExprLiteral(42, bind=False))
    )
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER, CHECK ("tbl"."id" > 42))'
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        'mysql',
    ],
    indirect=True,
)
async def test_foreign_key(txn: Transaction) -> None:
    """Test create table statement."""
    dst = Table('dst')
    await txn.exq(
        Query()
        .create_table(dst)
        .column('id', 'INTEGER')
        .column('lid', 'INTEGER')
        .unique()
        .column('mid', 'INTEGER')
        .unique()
        .unique_columns('lid', 'mid'),
    )

    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .column('lid', 'INTEGER')
        .column('mid', 'INTEGER')
        .foreign_key('lid', 'mid')
        .references(dst, tbl.lid, tbl.mid)
        .on_delete()
        .cascade()
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER, "lid" INTEGER, "mid" INTEGER,'
        ' FOREIGN KEY (lid, mid) REFERENCES "dst" ("lid", "mid") ON DELETE CASCADE'
        ')'
    )
    assert await txn.exq(query) == []


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        'postgres',
        pytest.param('mysql', marks=pytest.mark.skip(reason='unimplemented')),
    ],
    indirect=True,
)
async def test_foreign_key_deferrable(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = (
        Query()
        .create_table(tbl)
        .column('id', 'INTEGER')
        .column('lid', 'INTEGER')
        .column('mid', 'INTEGER')
        .foreign_key('lid', 'mid')
        .references(tbl, tbl.mid, tbl.lid)
        .deferrable()
        .unique_columns('lid', 'mid')
    )
    assert query.__getsql__()[0] == (
        'CREATE TABLE "tbl" '
        '("id" INTEGER, "lid" INTEGER, "mid" INTEGER,'
        ' FOREIGN KEY (lid, mid) REFERENCES "tbl" ("mid", "lid") DEFERRABLE,'
        ' UNIQUE (lid, mid)'
        ')'
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
async def test_without_rowid(txn: Transaction) -> None:
    """Test create table statement."""
    tbl = Table('tbl')
    query = Query().create_table(tbl).column('id', 'INTEGER').primary_key().without_rowid()
    assert query.__getsql__()[0] == 'CREATE TABLE "tbl" ("id" INTEGER PRIMARY KEY) WITHOUT ROWID'
    assert await txn.exq(query) == []
