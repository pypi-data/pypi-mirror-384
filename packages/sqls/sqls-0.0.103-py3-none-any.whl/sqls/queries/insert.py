# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL INSERT."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term
from .exceptions import QueryError
from .expr import Expr, ExprLiteral

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqls.interfaces import BindArg, SqlValue

    from .base import Texplicit
    from .expr import ExprColumn
    from .table import Tabular


class Insert(QBase[tuple[()]]):
    """INSERT mixin."""

    def _insert(self, cmd: str, table: Tabular) -> PostInsert:
        """Start 'action' INTO helper.

        Args:
            cmd: Action.
            table: Target table.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()
        return self._f(PostInsert, f'{cmd} INTO {sql}')

    def insert(self, table: Tabular) -> PostInsert:
        """Start INSERT INTO statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('INSERT', table)

    def replace(self, table: Tabular) -> PostInsert:
        """Start REPLACE INTO statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('REPLACE', table)

    def insert_or_replace(self, table: Tabular) -> PostInsert:
        """Start INSERT OR REPLACE INTO statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('INSERT OR REPLACE', table)

    def insert_or_rollback(self, table: Tabular) -> PostInsert:
        """Start INSERT OR ROLLBACK INTO statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('INSERT OR ROLLBACK', table)

    def insert_or_abort(self, table: Tabular) -> PostInsert:
        """Start INSERT OR ABORT statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('INSERT OR ABORT', table)

    def insert_or_fail(self, table: Tabular) -> PostInsert:
        """Start INSERT OR FAIL INTO statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('INSERT OR FAIL', table)

    def insert_or_ignore(self, table: Tabular) -> PostInsert:
        """Start INSERT OR IGNORE INTO statement.

        Args:
            table: Target table.

        Returns:
            Query builder.

        """
        return self._insert('INSERT OR IGNORE', table)


class Columns(QBase[tuple[()]]):
    """Columns mixin."""

    def columns(self, *cols: ExprColumn) -> PostColumns:
        """Add target columns.

        Args:
            cols: Columns.

        Returns:
            Query builder.

        """
        return self._f(PostColumns, f""" ({', '.join(f'"{x.col}"' for x in cols)})""")

    def default_values(self) -> PostValues:
        """Add DEFAULT VALUES clause."""
        return self._f(PostValues, ' DEFAULT VALUES')


class Values(QBase[tuple[()]]):
    """Values mixin."""

    def values(self, *vals: tuple[SqlValue | Expr, ...] | ExprLiteral) -> PostValues:
        """Add VALUES clause.

        Args:
            vals: Tuples of column values.

        Returns:
            Query builder.

        Raises:
            QueryError: If values empty or not nested sequence.

        """
        if not vals:
            msg = 'Values requires at least one row'
            raise QueryError(msg)

        if not vals[0]:
            msg = 'Values row requires at least one column'
            raise QueryError(msg)

        sqls = []
        args: list[BindArg] = []
        for val in vals:
            valex = val if isinstance(val, Expr) else ExprLiteral(val)
            sql, argz = valex.__getsql__()
            sqls.append(sql)
            args += argz
        return self._f(PostValues, f' VALUES{",".join(sqls)}', tuple(args))

    def select(self, select: QBase[Texplicit]) -> PostValues:
        """Add select query.

        Args:
            select: Select statement.

        Returns:
            Query builder.

        """
        sql, args = select.__getsql__()
        return self._f(PostValues, f' {sql}', args)


class Upsert(QBase[tuple[()]]):
    """UPSERT mixin."""

    def on_conflict(self, *cols: ExprColumn) -> PostUpsertColumns:
        """Start ON CONFLICT clause.

        Args:
            cols: Columns.

        Returns:
            Query builder.

        """
        sqls = []
        args: list[BindArg] = []
        for col in cols:
            sql, argz = col.__getsql__()
            sqls.append(sql)
            args += argz
        return self._f(PostUpsertColumns, f' ON CONFLICT ({", ".join(sqls)}) DO', tuple(args))

    def on_conflict_do_nothing(self) -> PostUpsert:
        """Add ON CONFLICT DO NOTHING clause."""
        return self._f(PostUpsert, ' ON CONFLICT DO NOTHING')


class UpsertUpdate(QBase[tuple[()]]):
    """UPDATE SET mixin."""

    def update_set(
        self,
        cols: Iterable[ExprColumn],
        vals: Iterable[Expr | int],
    ) -> PostUpsertUpdate:
        """Add UPDATE SET clause.

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
        for col, val in zip(cols, vals, strict=True):
            valex = val if isinstance(val, Expr) else ExprLiteral(val)
            sql, argz = valex.__getsql__()
            args += argz
            sqls.append(f'{col.col} = {sql}')
        return self._f(PostUpsertUpdate, f' UPDATE SET {", ".join(sqls)}', tuple(args))


class UpsertWhere(QBase[tuple[()]]):
    """WHERE mixin."""

    def where(self, expr: Expr) -> PostUpsertWhere:
        """Add WHERE clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostUpsertWhere, f' WHERE {sql}', args)


class PostInsert(
    Columns,
):
    """Post insert builder."""


class PostColumns(
    Values,
):
    """Post columns builder."""


class PostValues(
    Upsert,
    Term[tuple[()]],
):
    """Post values builder."""


class PostUpsert(
    Term[tuple[()]],
):
    """Post upsert builder."""


class PostUpsertColumns(
    UpsertUpdate,
):
    """Post upsert columns builder."""


class PostUpsertUpdate(
    UpsertWhere,
    Term[tuple[()]],
):
    """Post upsert update builder."""


class PostUpsertWhere(
    Term[tuple[()]],
):
    """Post upsert where builder."""
