# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL DELETE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from .expr import Expr
    from .table import Table


class Delete(QBase[tuple[()]]):
    """DELETE mixin."""

    def delete(self, table: Table) -> PostDelete:
        """Start DELETE statement.

        Args:
            table: Table to delete.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()
        return self._f(PostDelete, f'DELETE FROM {sql}')  # noqa: S608


class Where(QBase[tuple[()]]):
    """WHERE mixin."""

    def where(self, expr: Expr) -> PostWhere:
        """Add WHERE clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostWhere, f' WHERE {sql}', args)


class PostDelete(
    Where,
    Term[tuple[()]],
):
    """Post delete builder."""


class PostWhere(
    Term[tuple[()]],
):
    """Post where builder."""
