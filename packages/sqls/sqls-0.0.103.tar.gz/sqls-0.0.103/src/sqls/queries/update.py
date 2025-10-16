# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL UPDATE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term
from .exceptions import QueryError
from .expr import Expr, ExprColumn, ExprLiteral

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqls.interfaces import BindArg

    from .table import Table, Tabular


class Update(QBase[tuple[()]]):
    """UPDATE statement."""

    def _update(self, cmd: str, table: Table) -> PostUpdate:
        """Start UPDATE or 'action' helper.

        Args:
            cmd: Action.
            table: Target table.

        Returns:
            Query builder.

        """
        value, _ = table.__getsql__()
        return self._f(PostUpdate, f'UPDATE {cmd}{value}')

    def update(self, table: Table) -> PostUpdate:
        """Start UPDATE statement."""
        return self._update('', table)

    def update_or_rollback(self, table: Table) -> PostUpdate:
        """Start UPDATE OR ROLLBACK statement."""
        return self._update('OR ROLLBACK ', table)

    def update_or_abort(self, table: Table) -> PostUpdate:
        """Start UPDATE OR ABORT statement."""
        return self._update('OR ABORT ', table)

    def update_or_replace(self, table: Table) -> PostUpdate:
        """Start UPDATE OR REPLACE statement."""
        return self._update('OR REPLACE ', table)

    def update_or_fail(self, table: Table) -> PostUpdate:
        """Start UPDATE OR FAIL statement."""
        return self._update('OR FAIL ', table)

    def update_or_ignore(self, table: Table) -> PostUpdate:
        """Start UPDATE OR IGNORE statement."""
        return self._update('OR IGNORE ', table)


class Set(QBase[tuple[()]]):
    """SET mixin."""

    def set(
        self,
        cols: Iterable[ExprColumn],
        vals: Iterable[Expr | bool | bytes | int | float | str | None],
    ) -> PostSet:
        """Add SET clause.

        Args:
            cols: Columns.
            vals: Values.

        Returns:
            Query builder.

        Raises:
            QueryError: If column and value lengths differ.


        """
        cols = tuple(cols)
        vals = tuple(vals)
        if not cols or len(cols) != len(vals):
            msg = 'Columns and values need to have same length.'
            raise QueryError(msg)

        sqls = []
        args: list[BindArg] = []
        for val in vals:
            valex = val if isinstance(val, Expr) else ExprLiteral(val)
            sql, argz = valex.__getsql__()
            sqls.append(sql)
            args += argz

        assigns = [f'"{k.col}"={v}' for k, v in zip(cols, sqls, strict=True)]

        return self._f(PostSet, f' SET {", ".join(assigns)}', tuple(args))


class From(QBase[tuple[()]]):
    """FROM mixin."""

    def from_(self, table: Tabular) -> PostFrom:
        """Add FROM clause.

        Args:
            table: Table or subquery.

        Returns:
            Query builder.

        """
        sql, args = table.__getsql__()
        return self._f(PostFrom, f' FROM {sql}', args)


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


class PostUpdate(
    Set,
):
    """Post update builder."""


class PostSet(
    From,
    Where,
    Term[tuple[()]],
):
    """Post set builder."""


class PostFrom(
    Where,
    Term[tuple[()]],
):
    """Post from builder."""


class PostWhere(
    Term[tuple[()]],
):
    """Post where builder."""
