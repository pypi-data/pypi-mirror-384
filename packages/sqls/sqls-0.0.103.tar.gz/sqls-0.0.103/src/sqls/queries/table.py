# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL tables and joins."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .expr import Expr, ExprColumn

if TYPE_CHECKING:
    from typing import ClassVar, TypeVar

    from sqls.interfaces import BindArg, SqlValue
    from sqls.queries.base import QBase

    T = TypeVar('T', bound='JoinBase')


class Tabular:
    """Table base class."""

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        raise NotImplementedError


class Aliasable(Tabular):
    """Aliasable entity."""

    def as_(self, alias: str | Table) -> TableAlias:
        """Alias table.

        Args:
            alias: New table name.

        Returns:
            Aliased table.

        """
        return TableAlias(self, alias)

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        raise NotImplementedError  # pragma: no cover


class Table(Aliasable):
    """Database table."""

    def __init__(self, name: str, schema: str | None = None) -> None:
        """Initialize table.

        Args:
            name: Table name.
            schema: Schema name.

        """
        super().__init__()
        self._table = name
        self._schema = schema
        self.__star__ = ExprColumn(schema, name, '*')

    def __truediv__(self, key: str) -> ExprColumn:
        """Get column with expression '/' operator.

        Args:
            key: Column name.

        Returns:
            Column expression.

        """
        return ExprColumn(self._schema, self._table, key)

    def __getattr__(self, key: str) -> ExprColumn:
        """Get column expression from attribute access.

        Args:
            key: Column name.

        Returns:
            Column expression.

        """
        return ExprColumn(self._schema, self._table, key)

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        table = self._table.replace('"', '""')
        if self._schema:
            schema = self._schema.replace('"', '""')
            return f'"{schema}"."{table}"', ()
        return f'"{table}"', ()


class TableQuery(Aliasable):
    """Subquery used as table."""

    def __init__(self, query: QBase[tuple[SqlValue | object, ...]]) -> None:
        """Initialize table from subquery.

        Args:
            query: Subquery.

        """
        super().__init__()
        self.query = query

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        sql, args = self.query.__getsql__()
        return f'({sql})', args


class TableAlias(Tabular):
    """Tabular with applied alias."""

    def __init__(self, table: Tabular, alias: str | Table) -> None:
        """Initialize.

        Args:
            table: Table or TableQuery.
            alias: New table name.

        """
        super().__init__()
        self._tabular = table
        self._alias: str = alias if isinstance(alias, str) else alias._table  # noqa: SLF001
        self.__star__ = ExprColumn('', self._alias, '*')

    def __truediv__(self, key: str) -> ExprColumn:
        """Get column with expression '/' operator.

        Args:
            key: Column name.

        Returns:
            Column expression.

        """
        return ExprColumn(getattr(self._tabular, '_schema', ''), self._alias, key)

    def __getattr__(self, key: str) -> ExprColumn:
        """Get column expression from attribute access.

        Args:
            key: Column name.

        Returns:
            Column expression.

        """
        return ExprColumn(getattr(self._tabular, '_schema', ''), self._alias, key)

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        sql, args = self._tabular.__getsql__()
        tabular = getattr(self, '_tabular')  # noqa: B009
        if isinstance(tabular, JoinTerm):
            sql = f'({sql})'
        return f'{sql} AS "{self._alias}"', args


class JoinBase:
    """Base for JOIN clause builders."""

    _base: Tabular | JoinBase | None
    _joins: list[tuple[str, Tabular | JoinBase, Expr | None]]
    types: ClassVar[dict[str | None, str]] = {
        'cross': 'CROSS JOIN',
        'inner': 'INNER JOIN',
        'left': 'LEFT JOIN',
        None: 'JOIN',
    }

    def __init__(self, parent: JoinBase | None = None) -> None:
        """Initialize.

        Args:
            parent: Parent join object.

        """
        super().__init__()
        if parent:
            self._base = parent._base  # noqa: SLF001
            self._joins = parent._joins[:]  # noqa: SLF001
        else:
            self._base = None
            self._joins = []

    def _forward_join(self, cls: type[T], join: Tabular | JoinBase, typ: str) -> T:
        """Apply JOIN clause.

        Args:
            cls: Class of next builder in chain.
            join: Table or other Join.
            typ: Join type.

        Returns:
            Instance of next builder.

        """
        inst = cls(self)
        if self._base:
            inst._joins.append((typ, join, None))
        else:
            inst._base = join

        return inst

    def _forward_constraint(self, cls: type[T], expr: Expr) -> T:
        """Apply ON clause.

        Args:
            cls: Class of next builder in chain.
            expr: Expression to join on.

        Returns:
            Instance of next builder.

        """
        inst = cls(self)
        typ, table, _ = self._joins[-1]
        inst._joins[-1] = (typ, table, expr)
        return inst

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        assert self._base
        sql, args = self._base.__getsql__()
        for typ, table, expr in self._joins:
            sql += f' {typ} '
            subsql, subargs = table.__getsql__()
            sql += subsql
            args += subargs
            if expr:
                sql += ' ON '
                subsql, subargs = expr.__getsql__()
                sql += subsql
                args += subargs

        return sql, args


class Join(JoinBase):
    """JOIN builder."""

    def join(self, tabular: Tabular) -> JoinTerm:
        """Add first table to join.

        Args:
            tabular: Table, Subquery, or other Join.

        Returns:
            Join builder.

        """
        return self._forward_join(JoinTerm, tabular, '')


class JoinTerm(JoinBase, Aliasable):
    """Initial join state."""

    def join(self, tabular: Tabular, typ: str | None = None) -> JoinConstrainable:
        """JOIN tabular to current state.

        Args:
            tabular: Table, Subquery, or other Join.
            typ: Join type.

        Returns:
            Join builder.

        """
        return self._forward_join(JoinConstrainable, tabular, self.types[typ])


class JoinConstrainable(JoinTerm):
    """Constrainable join state."""

    def on_(self, expr: Expr) -> JoinTerm:
        """Constrain last JOIN with ON clause.

        Args:
            expr: Expression to join on.

        Returns:
            Join builder.

        """
        return self._forward_constraint(JoinTerm, expr)
