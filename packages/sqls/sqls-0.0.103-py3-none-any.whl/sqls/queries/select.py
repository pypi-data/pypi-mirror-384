# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL SELECT."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from .base import QBase, T_co, Term
from .exceptions import QueryError
from .expr import Expr, ExprAlias, ExprLiteral, ExprSubq, ExprTyped
from .table import TableQuery, Tabular

if TYPE_CHECKING:
    from sqls.interfaces import BindArg, SqlValue

    T_forward = TypeVar('T_forward', bound='tuple[SqlValue, ...]')
    T_query = TypeVar('T_query', bound='QBase[tuple[SqlValue, ...]]')

    _T1 = TypeVar('_T1', bound='SqlValue | object')
    _T2 = TypeVar('_T2', bound='SqlValue | object')
    _T3 = TypeVar('_T3', bound='SqlValue | object')
    _T4 = TypeVar('_T4', bound='SqlValue | object')
    _T5 = TypeVar('_T5', bound='SqlValue | object')
    _T6 = TypeVar('_T6', bound='SqlValue | object')
    _T7 = TypeVar('_T7', bound='SqlValue | object')
    _T8 = TypeVar('_T8', bound='SqlValue | object')
    _T9 = TypeVar('_T9', bound='SqlValue | object')
    _T10 = TypeVar('_T10', bound='SqlValue | object')
    _T11 = TypeVar('_T11', bound='SqlValue | object')
    _T12 = TypeVar('_T12', bound='SqlValue | object')
    _T13 = TypeVar('_T13', bound='SqlValue | object')
    _T14 = TypeVar('_T14', bound='SqlValue | object')
    _T15 = TypeVar('_T15', bound='SqlValue | object')
    _T16 = TypeVar('_T16', bound='SqlValue | object')


class Select(QBase[tuple[()]]):
    """SELECT mixin."""

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        __col11: ExprTyped[_T11],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10, _T11]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        __col11: ExprTyped[_T11],
        __col12: ExprTyped[_T12],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10, _T11, _T12]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        __col11: ExprTyped[_T11],
        __col12: ExprTyped[_T12],
        __col13: ExprTyped[_T13],
        /,
        distinct: bool = False,
    ) -> PostSelect[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10, _T11, _T12, _T13]]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        __col11: ExprTyped[_T11],
        __col12: ExprTyped[_T12],
        __col13: ExprTyped[_T13],
        __col14: ExprTyped[_T14],
        /,
        distinct: bool = False,
    ) -> PostSelect[
        tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10, _T11, _T12, _T13, _T14],
    ]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        __col11: ExprTyped[_T11],
        __col12: ExprTyped[_T12],
        __col13: ExprTyped[_T13],
        __col14: ExprTyped[_T14],
        __col15: ExprTyped[_T15],
        /,
        distinct: bool = False,
    ) -> PostSelect[
        tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10, _T11, _T12, _T13, _T14, _T15],
    ]: ...

    @overload
    def select(
        self,
        __col1: ExprTyped[_T1],
        __col2: ExprTyped[_T2],
        __col3: ExprTyped[_T3],
        __col4: ExprTyped[_T4],
        __col5: ExprTyped[_T5],
        __col6: ExprTyped[_T6],
        __col7: ExprTyped[_T7],
        __col8: ExprTyped[_T8],
        __col9: ExprTyped[_T9],
        __col10: ExprTyped[_T10],
        __col11: ExprTyped[_T11],
        __col12: ExprTyped[_T12],
        __col13: ExprTyped[_T13],
        __col14: ExprTyped[_T14],
        __col15: ExprTyped[_T15],
        __col16: ExprTyped[_T16],
        /,
        distinct: bool = False,
    ) -> PostSelect[
        tuple[
            _T1,
            _T2,
            _T3,
            _T4,
            _T5,
            _T6,
            _T7,
            _T8,
            _T9,
            _T10,
            _T11,
            _T12,
            _T13,
            _T14,
            _T15,
            _T16,
        ],
    ]: ...

    def select(  # type: ignore[misc]
        self,
        *columns: ExprTyped[SqlValue | object],
        distinct: bool = False,
    ) -> PostSelect[tuple[SqlValue, ...]]:
        """Start SELECT statement.

        Args:
            columns: Result columns.
            distinct: Is distinct query.

        Returns:
            Query builder.

        """
        pad = '' if not self._parent else ' '
        distinctstr = ' DISTINCT' if distinct else ''
        cols = []
        args: list[BindArg] = []
        for col in columns:
            sql, argz = col.__getsql__()
            cols.append(sql)
            args += argz
        sql = f'{pad}SELECT{distinctstr} {", ".join(cols)}'
        return self._f(PostSelect, sql, tuple(args))

    def values(self, *vals: T_forward) -> PostSelect[T_forward]:
        """Start VALUES clause.

        Args:
            vals: Result expressions.

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

        pad = '' if not self._parent else ' '
        row = f'({", ".join("?" * len(vals[0]))})'
        placeholder = ','.join([row] * len(vals))
        return self._f(PostSelect, f'{pad}VALUES{placeholder}', tuple(y for x in vals for y in x))


class From(QBase[T_co]):
    """FROM mixin."""

    def from_(self, table: Tabular) -> PostFrom[T_co]:
        """Add FROM clause.

        Args:
            table: Input table.

        Returns:
            Query builder.

        """
        assert isinstance(table, Expr | ExprAlias | Tabular), f'From param is not tabular, {table}'
        sql, args = table.__getsql__()
        return self._f(PostFrom, f' FROM {sql}', args)


class Where(QBase[T_co]):
    """WHERE mixin."""

    def where(self, expr: Expr | None) -> PostWhere[T_co]:
        """Add WHERE clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        if expr is None:
            return PostWhere(self)
        sql, args = expr.__getsql__()
        return self._f(PostWhere, f' WHERE {sql}', args)


class Groupby(QBase[T_co]):
    """GROUP BY mixin."""

    def group_by(self, *exprs: Expr) -> PostGroupby[T_co]:
        """Add GROUP BY clause.

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
        return self._f(PostGroupby, f' GROUP BY {", ".join(sqls)}', tuple(args))


class Having(QBase[T_co]):
    """HAVING mixin."""

    def having(self, expr: Expr) -> PostHaving[T_co]:
        """Add HAVING clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostHaving, f' HAVING {sql}', args)


class Compound(QBase[T_co]):
    """Compound mixin."""

    def union(self) -> PostCompound:
        """Add UNION query."""
        return self._f(PostCompound, ' UNION')

    def union_query(self, other: T_query) -> T_query:
        """Add UNION query.

        Args:
            other: Select statement.

        Returns:
            Query builder.

        """
        assert isinstance(other, QBase)
        copy = self._f(other.__class__, ' UNION ')
        copy._append(other)  # noqa: SLF001
        return copy

    def union_all(self) -> PostCompound:
        """Add UNION ALL query."""
        return self._f(PostCompound, ' UNION ALL')

    def intersect(self) -> PostCompound:
        """Add INTERSECT query."""
        return self._f(PostCompound, ' INTERSECT')

    def except_(self) -> PostCompound:
        """Add EXCEPT query."""
        return self._f(PostCompound, ' EXCEPT')


class Order(QBase[T_co]):
    """ORDER mixin."""

    def order_by(
        self,
        *exprs: Expr,
        desc: bool = False,
        nulls: str | None = None,
    ) -> PostOrder[T_co]:
        """Add ORDER BY clause.

        Args:
            exprs: Expressions.
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
        sort = ' DESC' if desc else ''
        nulls = '' if nulls is None else f' NULLS {nulls}'
        return self._f(PostOrder, f' ORDER BY {", ".join(sqls)}{sort}{nulls}', tuple(args))


class Limit(QBase[T_co]):
    """LIMIT mixin."""

    def limit(self, expr: int | Expr) -> PostLimit[T_co]:
        """Add LIMIT clause.

        Args:
            expr: Item limit.

        Returns:
            Query builder.

        """
        if not isinstance(expr, Expr):
            expr = ExprLiteral(expr)
        sql, args = expr.__getsql__()
        return self._f(PostLimit, f' LIMIT {sql}', args)


class Offset(QBase[T_co]):
    """OFFSET mixin."""

    def offset(self, expr: int | Expr) -> PostOffset[T_co]:
        """Add OFFSET clause.

        Args:
            expr: Item offset.

        Returns:
            Query builder.

        """
        if not isinstance(expr, Expr):
            expr = ExprLiteral(expr)
        sql, args = expr.__getsql__()
        return self._f(PostOffset, f' OFFSET {sql}', args)


class SelectTerm(Term[T_co]):
    """Select terminal state mixin."""

    def subq(self) -> ExprSubq[T_co]:
        """Convert to subquery expression."""
        return ExprSubq(self)

    def table(self) -> TableQuery:
        """Convert to subquery table."""
        return TableQuery(self)


class PostSelect(
    From[T_co],
    Where[T_co],
    Groupby[T_co],
    Having[T_co],
    Compound[T_co],
    Order[T_co],
    Limit[T_co],
    SelectTerm[T_co],
):
    """Post select builder."""


class PostFrom(
    Where[T_co],
    Groupby[T_co],
    Having[T_co],
    Compound[T_co],
    Order[T_co],
    Limit[T_co],
    SelectTerm[T_co],
):
    """Post from builder."""


class PostWhere(
    Groupby[T_co],
    Having[T_co],
    Compound[T_co],
    Order[T_co],
    Limit[T_co],
    SelectTerm[T_co],
):
    """Post where builder."""


class PostGroupby(
    Having[T_co],
    Compound[T_co],
    Order[T_co],
    Limit[T_co],
    SelectTerm[T_co],
):
    """Post groupby builder."""


class PostHaving(
    Compound[T_co],
    Order[T_co],
    Limit[T_co],
    SelectTerm[T_co],
):
    """Post having builder."""


class PostCompound(
    Select,
):
    """Post compound builder."""


class PostOrder(
    Limit[T_co],
    SelectTerm[T_co],
):
    """Post order builder."""


class PostLimit(
    Offset[T_co],
    SelectTerm[T_co],
):
    """Post limit builder."""


class PostOffset(
    SelectTerm[T_co],
):
    """Post offset builder."""
