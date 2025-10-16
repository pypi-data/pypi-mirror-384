# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL window expressions."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from sqls.queries.base import QBase, Term
from sqls.queries.expr import Expr, ExprTyped

if TYPE_CHECKING:
    from sqls.interfaces import BindArg

T = TypeVar('T')


class Window(QBase[tuple[()]]):
    """WINDOW function mixin."""

    def execute(self, funcname: str, *exprs: Expr) -> PostExecute:
        """Start WINDOW function invocation.

        Args:
            funcname: Function name.
            exprs: Function arguments.

        Returns:
            Query builder.

        """
        sqls = []
        args: list[BindArg] = []
        for expr in exprs:
            sql, argz = expr.__getsql__()
            sqls.append(sql)
            args += argz
        return self._f(PostExecute, f'{funcname}({", ".join(sqls)})', tuple(args))


class Filter(QBase[tuple[()]]):
    """FILTER mixin."""

    def filter(self, expr: Expr) -> Over:
        """Add FILTER clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(Over, f' FILTER (WHERE {sql})', args)


class Over(QBase[tuple[()]]):
    """OVER mixin."""

    def over_name(self, name: str) -> WindowTerm:
        """Add OVER window name clause.

        Args:
            name: Window name.

        Returns:
            Query builder.

        """
        return self._f(WindowTerm, f' OVER {name}', ())

    def over_definition(self) -> PostOver:
        """Add OVER window definition clause.

        Returns:
            Query builder.

        """
        enter = ((Term,), ')')
        return self._f(PostOver, ' OVER (', enter=enter)


class BaseWindow(QBase[tuple[()]]):
    """Base window mixin."""

    def base_window(self, name: str) -> PostBaseWindow:
        """Add base window name.

        Copies partition and order from base window.

        Args:
            name: Window name.

        Returns:
            Query builder.

        """
        return self._f(PostBaseWindow, f'{name}', ())


class WindowTerm(QBase[tuple[()]], Expr):
    """Window term mixin."""

    def endq(self) -> Term[tuple[()]]:
        """Mark window function statement done."""
        return Term(self)

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert function invocation to typed expression.

        Args:
            _: Type argument.

        Returns:
            Typed column expression.

        """
        return ExprTyped[T](self)


class PartitionBy(QBase[tuple[()]]):
    """PARTITION BY mixin."""

    def partition_by(self, *exprs: Expr) -> PostPartitionBy:
        """Add PARTITION BY clause.

        Args:
            exprs: Expressions.

        Returns:
            Query builder.

        """
        sqls = []
        args: list[BindArg] = []
        for expr in exprs:
            sql, argz = expr.__getsql__()
            sqls.append(sql)
            args += argz
        return self._f(PostPartitionBy, f' PARTITION BY {", ".join(sqls)}', tuple(args))


class OrderBy(QBase[tuple[()]]):
    """ORDER BY mixin."""

    def order_by(
        self,
        *exprs: Expr,
        collate: str | None = None,
        desc: bool = False,
        nulls: str | None = None,
    ) -> PostOrderBy:
        """Add ORDER BY clause.

        Args:
            exprs: Expressions.
            collate: Collation.
            desc: Sort descending.
            nulls: NULLS keyword to add.

        Returns:
            Query builder.

        """
        sqls = []
        args: list[BindArg] = []
        for expr in exprs:
            sql, argz = expr.__getsql__()
            sqls.append(sql)
            args += argz
        collation = f' COLLATE {collate}' if collate else ''
        sort = ' DESC' if desc else ''
        nulls = '' if nulls is None else f' NULLS {nulls}'
        return self._f(
            PostOrderBy,
            f' ORDER BY {", ".join(sqls)}{collation}{sort}{nulls}',
            tuple(args),
        )


class FrameType(QBase[tuple[()]]):
    """Frame type mixin."""

    def range(self) -> FrameBoundary:
        """Add RANGE clause."""
        return self._f(FrameBoundary, ' RANGE', ())

    def rows(self) -> FrameBoundary:
        """Add ROWS clause."""
        return self._f(FrameBoundary, ' ROWS', ())

    def groups(self) -> FrameBoundary:
        """Add GROUPS clause."""
        return self._f(FrameBoundary, ' GROUPS', ())


class FrameBoundary(QBase[tuple[()]]):
    """Frame boundary."""

    def between(self) -> FrameBoundaryStart:
        """Start BETWEEN clause."""
        return self._f(FrameBoundaryStart, ' BETWEEN', ())

    def precedeing(self, expr: Expr | None = None) -> PostFrameBoundary:
        """Add PRECEDING clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql = ''
        args: list[BindArg] = []
        if expr is None:
            sql += ' UNBOUNDED PRECEDING'
        else:
            subsql, subargs = expr.__getsql__()
            sql += f' {subsql} PRECEDING'
            args += subargs
        return self._f(PostFrameBoundary, sql, tuple(args))

    def current_row(self) -> PostFrameBoundary:
        """Add CURRENT ROW clause."""
        return self._f(PostFrameBoundary, ' CURRENT ROW', ())


class FrameBoundaryStart(QBase[tuple[()]]):
    """Frame boundary start mixin."""

    def precedeing(self, expr: Expr | None = None) -> FrameBoundaryEnd:
        """Add PRECEDING clause for frame start.

        Args:
            expr: Expression or None for UNBOUNDED.

        Returns:
            Query builder.

        """
        sql = ''
        args: list[BindArg] = []
        if expr is None:
            sql += ' UNBOUNDED PRECEDING AND'
        else:
            subsql, subargs = expr.__getsql__()
            sql += f' {subsql} PRECEDING AND'
            args += subargs
        return self._f(FrameBoundaryEnd, sql, tuple(args))

    def current_row(self) -> FrameBoundaryEnd:
        """Add CURRENT ROW clause for frame start."""
        return self._f(FrameBoundaryEnd, ' CURRENT ROW AND', ())

    def following(self, expr: Expr) -> FrameBoundaryEnd:
        """Add FOLLOWING clause for frame start.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(FrameBoundaryEnd, f' {sql} FOLLOWING AND', args)


class FrameBoundaryEnd(QBase[tuple[()]]):
    """Frame boundary end mixin."""

    def precedeing(self, expr: Expr) -> PostFrameBoundary:
        """Add PRECEDING clause for frame end.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostFrameBoundary, f' {sql} PRECEDING', args)

    def current_row(self) -> PostFrameBoundary:
        """Add CURRENT ROW clause for frame end."""
        return self._f(PostFrameBoundary, ' CURRENT ROW', ())

    def following(self, expr: Expr | None = None) -> PostFrameBoundary:
        """Add FOLLOWING clause for frame end.

        Args:
            expr: Expression or None for UNBOUNDED.

        Returns:
            Query builder.

        """
        sql = ''
        args: list[BindArg] = []
        if expr is None:
            sql += ' UNBOUNDED FOLLOWING'
        else:
            subsql, subargs = expr.__getsql__()
            sql += f' {subsql} FOLLOWING'
            args += subargs
        return self._f(PostFrameBoundary, sql, tuple(args))


class Exclude(QBase[tuple[()]]):
    """EXCLUDE mixin."""

    def exclude_no_others(self) -> WindowTerm:
        """Add EXCLUDE NO OTHERS clause."""
        return self._f(WindowTerm, ' EXCLUDE NO OTHERS', ())

    def exclude_current_row(self) -> WindowTerm:
        """Add EXCLUDE CURRENT ROW clause."""
        return self._f(WindowTerm, ' EXCLUDE CURRENT ROW', ())

    def exclude_group(self) -> WindowTerm:
        """Add EXCLUDE GROUP clause."""
        return self._f(WindowTerm, ' EXCLUDE GROUP', ())

    def exclude_ties(self) -> WindowTerm:
        """Add EXCLUDE TIES clause."""
        return self._f(WindowTerm, ' EXCLUDE TIES', ())


class PostFrameBoundary(
    Exclude,
    WindowTerm,
):
    """Post frame boundary builder."""


class PostExecute(
    Filter,
    Over,
):
    """Post execute builder."""


class PostOver(
    BaseWindow,
    PartitionBy,
    OrderBy,
    FrameType,
    WindowTerm,
):
    """Post over builder."""


class PostBaseWindow(
    PartitionBy,
    OrderBy,
    FrameType,
    WindowTerm,
):
    """Post basewindow builder."""


class PostPartitionBy(
    OrderBy,
    FrameType,
    WindowTerm,
):
    """Post partitionby builder."""


class PostOrderBy(
    FrameType,
    WindowTerm,
):
    """Post orderby builder."""
