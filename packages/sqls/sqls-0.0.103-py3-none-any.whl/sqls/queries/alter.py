# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL ALTER."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term
from .create_table import (
    ColumnConstraintGeneric,
    DeferrableGeneric,
    OnConflictGeneric,
    OnRefchangeActionGeneric,
    OnRefchangeGeneric,
)

if TYPE_CHECKING:
    from .expr import ExprColumn
    from .table import Table


class Alter(QBase[tuple[()]]):
    """ALTER TABLE mixin."""

    def alter_table(self, table: Table) -> PostAlter:
        """Start ALTER TABLE statement."""
        return self._f(PostAlter, f'ALTER TABLE {table.__getsql__()[0]}')


class Rename(QBase[tuple[()]]):
    """RENAME mixin."""

    def rename_to(self, table: Table) -> PostRename:
        """Add RENAME TO clause.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._f(PostRename, f' RENAME TO {table.__getsql__()[0]}')

    def rename_column(self, old: ExprColumn, new: ExprColumn) -> PostRename:
        """Add RENAME COLUMN clause.

        Args:
            old: Old column.
            new: New column.

        Returns:
            Query builder.

        """
        oldcol = old.col.replace('"', '""')
        newcol = new.col.replace('"', '""')
        return self._f(PostRename, f' RENAME COLUMN "{oldcol}" TO "{newcol}"')


class Drop(QBase[tuple[()]]):
    """DROP mixin."""

    def drop_column(self, col: ExprColumn) -> PostDrop:
        """Add DROP COLUMN clause.

        Args:
            col: Column.

        Returns:
            Query builder.

        """
        newcol = col.col.replace('"', '""')
        return self._f(PostDrop, f' DROP COLUMN "{newcol}"')


class Add(QBase[tuple[()]]):
    """ADD COLUMN mixin."""

    def add_column(self, column: ExprColumn, typ: str | None) -> PostAdd:
        """Start ADD COLUMN clause.

        Args:
            column: Column.
            typ: Column type.

        Returns:
            Query builder.

        """
        col = column.col.replace('"', '""')
        typ = f' {typ}' if typ else ''
        return self._f(PostAdd, f' ADD COLUMN {col}{typ}')


class ColumnConstraint(
    ColumnConstraintGeneric[
        'PostColumnConstraint',
        'PostAdd',
        'PostColumnConstraintReferences',
    ],
):
    """Column constraint."""


class OnRefchange(OnRefchangeGeneric['OnRefchangeAction']):
    """On reference change mixin."""


class OnRefchangeAction(OnRefchangeActionGeneric['PostColumnConstraintReferences']):
    """On reference change action mixin."""


class Deferrable(DeferrableGeneric['PostAdd']):
    """Deferrable mixin."""


class ConflictClause(OnConflictGeneric['PostAdd']):
    """Conflict clause mixin."""


class PostAlter(
    Rename,
    Drop,
    Add,
):
    """Post ALTER builder."""


class PostRename(
    Term[tuple[()]],
):
    """Post RENAME builder."""


class PostDrop(
    Term[tuple[()]],
):
    """Post DROP builder."""


class PostAdd(
    ColumnConstraint,
    Term[tuple[()]],
):
    """Post ADD builder."""


class PostColumnConstraint(
    PostAdd,
    ConflictClause,
):
    """Post ColumnConstraint builder."""


class PostColumnConstraintReferences(
    PostAdd,
    OnRefchange,
    Deferrable,
):
    """Post ColumnConstraintReferences builder."""


class PostConflictClause(
    PostAdd,
):
    """Post ConflictClause builder."""
