# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL CREATE INDEX."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from .expr import Expr, ExprColumn
    from .table import Table


class CreateIndex(QBase[tuple[()]]):
    """CREATE INDEX mixin."""

    def create_index(
        self,
        index: Table,
        table: Table,
        *cols: ExprColumn,
        unique: bool = False,
        if_not_exists: bool = False,
    ) -> PostCreate:
        """Start CREATE INDEX statement.

        Args:
            index: New index table.
            table: Table to index over.
            cols: Columns to index.
            unique: Should index be unique.
            if_not_exists: Ignore if index exists.

        Returns:
            Query.

        """
        isql, _ = index.__getsql__()
        tsql, _ = table.__getsql__()

        def colname(col: ExprColumn) -> str:
            return f'"{col.col}"'

        colstr = f'({", ".join(colname(x) for x in cols)})'
        unq = ' UNIQUE' if unique else ''
        ine = ' IF NOT EXISTS' if if_not_exists else ''
        sql = f'CREATE{unq} INDEX{ine} {isql} ON {tsql} {colstr}'
        return self._f(PostCreate, sql)


class Where(QBase[tuple[()]]):
    """WHERE mixin."""

    def where(self, expr: Expr) -> PostWhere:
        """Add WHERE clause.

        Args:
            expr: Expression.

        Returns:
            Query.

        """
        sql, args = expr.__getsql__()
        return self._f(PostWhere, f' WHERE {sql}', args)


class PostCreate(
    Where,
    Term[tuple[()]],
):
    """Post CREATE mixin."""


class PostWhere(
    Term[tuple[()]],
):
    """Post WHERE mixin."""
