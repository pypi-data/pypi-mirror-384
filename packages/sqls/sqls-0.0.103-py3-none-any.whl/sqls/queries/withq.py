# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL WITH."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term
from .delete import Delete
from .insert import Insert
from .select import Select
from .update import Update

if TYPE_CHECKING:
    from .base import Texplicit
    from .expr import ExprColumn
    from .table import Table


class With(QBase[tuple[()]]):
    """WITH mixin."""

    def with_(self, table: Table, *cols: ExprColumn, recursive: bool = False) -> As:
        """Start WITH clause.

        Args:
            table: Table.
            cols: Table columns.
            recursive: Allow recursive queries.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()
        rec = ' RECURSIVE' if recursive else ''
        sql = f'WITH{rec} {sql} ({", ".join(x.col for x in cols)})'
        return self._f(As, sql)


class As(QBase[tuple[()]]):
    """AS mixin for WITH."""

    def as_(self, expr: QBase[Texplicit]) -> PostAs:
        """Add AS clause.

        Args:
            expr: Common table expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostAs, f' AS ({sql})', args)


class AddWith(QBase[tuple[()]]):
    """WITH mixin for adding additional with clauses."""

    def with_(self, table: Table, *cols: ExprColumn) -> As:
        """Start WITH clause.

        Args:
            table: Table.
            cols: Table columns.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()
        return self._f(As, f', {sql} ({", ".join(x.col for x in cols)})')


class PostAs(
    AddWith,
    Delete,
    Insert,
    Select,
    Update,
    Term[tuple[()]],
):
    """Post AS Builder."""
