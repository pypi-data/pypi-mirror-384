# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Models declarative layer tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from sqls.models import (
    CharField,
    Fieldmeta,
    ForeignKeyField,
    IntegerField,
    Model,
    Tablemeta,
    get_create_queries,
)
from sqls.models.model import Indexmeta


def get_q(*models: type[Model]) -> list[str]:
    """Convert models to create statements."""
    queries = get_create_queries(models)
    return [x.__getsql__()[0] for x in queries]


def test_simple_declaration() -> None:
    """Test simple field."""

    @dataclass
    class Node(Model):
        """Test model."""

        num: IntegerField

    assert get_q(Node) == [
        (
            'CREATE TABLE IF NOT EXISTS "node" '
            '("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "num" INTEGER NOT NULL)'
        ),
    ]


def test_annotated_declaration() -> None:
    """Test annotated field."""

    @dataclass
    class Node(Model):
        """Test model."""

        text: Annotated[CharField, Fieldmeta(max_length=32)]

    assert get_q(Node) == [
        (
            'CREATE TABLE IF NOT EXISTS "node" '
            '("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "text" VARCHAR(32) NOT NULL)'
        ),
    ]


def test_unique_fields() -> None:
    """Test unique fields."""

    @dataclass
    class Node(Model):
        """Test model."""

        optional: IntegerField | None
        unique: Annotated[IntegerField, Fieldmeta(unique=True)]
        unique_optional: Annotated[IntegerField, Fieldmeta(unique=True)] | None

    assert get_q(Node) == [
        (
            'CREATE TABLE IF NOT EXISTS "node" '
            '("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "optional" INTEGER, "unique" '
            'INTEGER NOT NULL UNIQUE, "unique_optional" INTEGER UNIQUE)'
        ),
    ]


def test_default_value() -> None:
    """Test unique fields."""

    @dataclass
    class Node(Model):
        """Test model."""

        defaulted: Annotated[IntegerField, Fieldmeta(default=42)]

    assert get_q(Node) == [
        (
            'CREATE TABLE IF NOT EXISTS "node" '
            '("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'
            ' "defaulted" INTEGER NOT NULL DEFAULT 42)'
        ),
    ]


def test_foreignkey_selfreference() -> None:
    """Test self references."""

    @dataclass
    class Node(Model):
        """Test model."""

        node_id: ForeignKeyField
        parent: Annotated[ForeignKeyField, Fieldmeta(foreign_key=('node', 'id'))]

    assert get_q(Node) == [
        'CREATE TABLE IF NOT EXISTS "node" '
        '("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'
        ' "node_id" INTEGER NOT NULL REFERENCES "node" ("id") ON DELETE CASCADE,'
        ' "parent" INTEGER NOT NULL REFERENCES "node" ("id") ON DELETE CASCADE)',
        'CREATE INDEX IF NOT EXISTS "idx__node__node_id" ON "node" ("node_id")',
        'CREATE INDEX IF NOT EXISTS "idx__node__parent" ON "node" ("parent")',
    ]
    assert Node.__model__['backward_rels'] == [(Node, 'node_id', 'id'), (Node, 'parent', 'id')]
    assert Node.__model__['forward_rels'] == [(Node, 'id', 'node_id'), (Node, 'id', 'parent')]


def test_foreignkey_reference() -> None:
    """Test references."""

    @dataclass
    class Parent(Model):
        """Test model."""

    @dataclass
    class Child(Model):
        """Test model."""

        parent_id: ForeignKeyField

    assert get_q(Parent, Child) == [
        'CREATE TABLE IF NOT EXISTS "parent" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS "child" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
        '"parent_id" INTEGER NOT NULL REFERENCES "parent" ("id") ON DELETE CASCADE)',
        'CREATE INDEX IF NOT EXISTS "idx__child__parent_id" ON "child" ("parent_id")',
    ]
    assert Parent.__model__['backward_rels'] == [(Child, 'parent_id', 'id')]
    assert Child.__model__['forward_rels'] == [(Parent, 'id', 'parent_id')]


def test_foreignkey_reference_with_on_delete() -> None:
    """Test on delete clause."""

    @dataclass
    class Parent(Model):
        """Test model."""

    @dataclass
    class Child(Model):
        """Test model."""

        parent_id: Annotated[ForeignKeyField, Fieldmeta(on_delete='RESTRICT')]

    assert get_q(Parent, Child) == [
        'CREATE TABLE IF NOT EXISTS "parent" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS "child" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
        '"parent_id" INTEGER NOT NULL REFERENCES "parent" ("id") ON DELETE RESTRICT)',
        'CREATE INDEX IF NOT EXISTS "idx__child__parent_id" ON "child" ("parent_id")',
    ]
    assert Parent.__model__['backward_rels'] == [(Child, 'parent_id', 'id')]
    assert Child.__model__['forward_rels'] == [(Parent, 'id', 'parent_id')]

    @dataclass
    class Child2(Model):
        """Test model."""

        parent_id: Annotated[ForeignKeyField, Fieldmeta(on_delete='SET DEFAULT')]

    assert get_q(Parent, Child2) == [
        'CREATE TABLE IF NOT EXISTS "parent" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS "child2" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
        '"parent_id" INTEGER NOT NULL REFERENCES "parent" ("id") ON DELETE SET DEFAULT)',
        'CREATE INDEX IF NOT EXISTS "idx__child2__parent_id" ON "child2" ("parent_id")',
    ]

    @dataclass
    class Child3(Model):
        """Test model."""

        parent_id: Annotated[ForeignKeyField, Fieldmeta(on_delete='SET NULL')]

    assert get_q(Parent, Child3) == [
        'CREATE TABLE IF NOT EXISTS "parent" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS "child3" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
        '"parent_id" INTEGER NOT NULL REFERENCES "parent" ("id") ON DELETE SET NULL)',
        'CREATE INDEX IF NOT EXISTS "idx__child3__parent_id" ON "child3" ("parent_id")',
    ]


def test_foreignkey_reference_with_idfield() -> None:
    """Test self references."""

    @dataclass
    class Node(Model):
        """Test model."""

        id: Annotated[ForeignKeyField, Fieldmeta(foreign_key=('node', 'id'))]

    assert get_q(Node) == [
        'CREATE TABLE IF NOT EXISTS "node" '
        '("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL'
        ' REFERENCES "node" ("id") ON DELETE CASCADE)',
    ]
    assert Node.__model__['backward_rels'] == [(Node, 'id', 'id')]
    assert Node.__model__['forward_rels'] == [(Node, 'id', 'id')]


def test_through_reference() -> None:
    """Test references."""

    @dataclass
    class User(Model):
        """Test model."""

    @dataclass
    class Group(Model):
        """Test model."""

    @dataclass
    class UserGroup(Model):
        """Test model."""

        __noid__ = True
        user_id: ForeignKeyField
        group_id: ForeignKeyField

    assert get_q(User, Group, UserGroup) == [
        'CREATE TABLE IF NOT EXISTS "user" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS "group" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS "user_group" ('
        '"user_id" INTEGER NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE, '
        '"group_id" INTEGER NOT NULL REFERENCES "group" ("id") ON DELETE CASCADE)',
        'CREATE INDEX IF NOT EXISTS "idx__user_group__user_id" ON "user_group" ("user_id")',
        'CREATE INDEX IF NOT EXISTS "idx__user_group__group_id" ON "user_group" ("group_id")',
    ]
    assert User.__model__['through_rels'] == [(UserGroup, 'user_id', 'id', Group, 'id', 'group_id')]
    assert Group.__model__['through_rels'] == [(UserGroup, 'group_id', 'id', User, 'id', 'user_id')]
    assert not UserGroup.__model__['forward_rels']
    assert not UserGroup.__model__['backward_rels']


def test_compound_index() -> None:
    """Test compound index."""

    @dataclass
    class UserGroup(Model):
        """Test model."""

        __tablemeta__ = Tablemeta(
            indexes=(Indexmeta(fields=('user_id', 'group_id'), unique=False),),
        )

        __noid__ = True
        user_id: IntegerField
        group_id: IntegerField

    assert get_q(UserGroup) == [
        'CREATE TABLE IF NOT EXISTS "user_group" ('
        '"user_id" INTEGER NOT NULL, '
        '"group_id" INTEGER NOT NULL)',
        'CREATE INDEX IF NOT EXISTS "idx__user_group__user_id__group_id" ON '
        '"user_group" ("user_id", "group_id")',
    ]


def test_compound_unique_index() -> None:
    """Test compound unique index."""

    @dataclass
    class UserGroup(Model):
        """Test model."""

        __tablemeta__ = Tablemeta(indexes=(Indexmeta(fields=('user_id', 'group_id'), unique=True),))

        __noid__ = True
        user_id: IntegerField
        group_id: IntegerField

    assert get_q(UserGroup) == [
        'CREATE TABLE IF NOT EXISTS "user_group" ('
        '"user_id" INTEGER NOT NULL, '
        '"group_id" INTEGER NOT NULL)',
        'CREATE UNIQUE INDEX IF NOT EXISTS "idx__user_group__user_id__group_id" ON '
        '"user_group" ("user_id", "group_id")',
    ]
