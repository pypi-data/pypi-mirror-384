# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL expressions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from .exceptions import QueryError

if TYPE_CHECKING:
    from typing import TypeAlias

    from sqls.interfaces import BindArg, Query, SqlValue

    Other: TypeAlias = 'tuple[SqlValue, ...] | SqlValue | Expr'

T = TypeVar('T')


def fmt(value: SqlValue) -> str:
    """Format value for SQL string.

    Args:
        value: Value to format.

    Returns:
        Formatted value.

    Raises:
        QueryError: If bytes passed as value.

    """
    if isinstance(value, int | float):
        return repr(value)

    if isinstance(value, bytes):  # pragma: no cover
        raise QueryError

    assert isinstance(value, str)
    value = value.replace("'", "''")
    return f"'{value}'"


class ExprTyped(Generic[T]):
    """Typed Expression."""

    def __init__(self, child: Expr | ExprAlias) -> None:
        """Initialize.

        Args:
            child: Expression.

        """
        super().__init__()
        self.child = child

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        return self.child.__getsql__()


class Expr:
    """SQL Expression."""

    def positive(self) -> ExprUnary:
        """Make positive."""
        return ExprUnary('+', self)

    def negative(self) -> ExprUnary:
        """Make negative."""
        return ExprUnary('-', self)

    def bitwise_negate(self) -> ExprUnary:
        """Bitwise negation."""
        return ExprUnary('~', self)

    def negate(self) -> ExprUnary:
        """Negate expression."""
        return ExprUnary('NOT', self)

    def strconcat(self, other: Other) -> ExprBinary:
        """Concatenate other string."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('||', self, other)

    def __mul__(self, other: Other) -> ExprBinary:
        """Multiply."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('*', self, other)

    def __truediv__(self, other: Other) -> ExprBinary:
        """Divide."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('/', self, other)

    def __mod__(self, other: Other) -> ExprBinary:
        """Modulo."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('%', self, other)

    def __add__(self, other: Other) -> ExprBinary:
        """Add."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('+', self, other)

    def __sub__(self, other: Other) -> ExprBinary:
        """Subtract."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('-', self, other)

    def __lshift__(self, other: Other) -> ExprBinary:
        """Left shift."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('<<', self, other)

    def __rshift__(self, other: Other) -> ExprBinary:
        """Right shift."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('>>', self, other)

    def __and__(self, other: Other) -> ExprBinary:
        """Binary and."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('&', self, other)

    def __or__(self, other: Other) -> ExprBinary:
        """Binary or."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('|', self, other)

    def __lt__(self, other: Other) -> ExprBinary:
        """Compare lt."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('<', self, other)

    def __le__(self, other: Other) -> ExprBinary:
        """Compare le."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('<=', self, other)

    def __gt__(self, other: Other) -> ExprBinary:
        """Compare gt."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('>', self, other)

    def __ge__(self, other: Other) -> ExprBinary:
        """Compare ge."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('>=', self, other)

    def __eq__(self, other: Other) -> ExprBinary:  # type: ignore[override]
        """Compare eq."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('=', self, other)

    def __ne__(self, other: Other) -> ExprBinary:  # type: ignore[override]
        """Compare ne."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('!=', self, other)

    def and_(self, other: Other) -> ExprBinary:
        """Compare and."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('AND', self, other)

    def or_(self, other: Other) -> ExprBinary:
        """Compare or."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('OR', self, other)

    def cast(self, typ: str) -> ExprFlexible:
        """Cast."""
        return ExprFlexible('CAST (', self, f' AS {typ})')

    def _match(self, match: str, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Create match expression and optional escape.

        Args:
            match: Match function.
            expr: Expression to match.
            escape: Escape character.

        Returns:
            Match Expression.

        """
        if not isinstance(expr, Expr):
            expr = ExprLiteral(expr)
        esc = (f' ESCAPE {escape!r}',) if escape else ()
        return ExprFlexible(self, f' {match} ', expr, *esc)

    def like(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Like."""
        return self._match('LIKE', expr, escape)

    def not_like(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Not like."""
        return self._match('NOT LIKE', expr, escape)

    def glob(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Glob."""
        return self._match('GLOB', expr, escape)

    def not_glob(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Not glob."""
        return self._match('NOT GLOB', expr, escape)

    def regexp(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Regexp."""
        return self._match('REGEXP', expr, escape)  # pragma: no cover

    def not_regexp(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Not regexp."""
        return self._match('NOT REGEXP', expr, escape)  # pragma: no cover

    def match(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Match."""
        return self._match('MATCH', expr, escape)  # pragma: no cover

    def not_match(self, expr: Other, escape: str | None = None) -> ExprFlexible:
        """Not match."""
        return self._match('NOT MATCH', expr, escape)  # pragma: no cover

    def is_null(self) -> ExprFlexible:
        """Is null."""
        return ExprFlexible(self, ' IS NULL')

    def not_null(self) -> ExprFlexible:
        """Is not null."""
        return ExprFlexible(self, ' IS NOT NULL')

    def is_(self, other: Other) -> ExprBinary:
        """Compare is."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('IS', self, other)

    def is_not(self, other: Other) -> ExprBinary:
        """Compare is not."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('IS NOT', self, other)

    def between(self, expr1: Other, expr2: Other) -> ExprFlexible:
        """Between."""
        if not isinstance(expr1, Expr):
            expr1 = ExprLiteral(expr1)
        if not isinstance(expr2, Expr):
            expr2 = ExprLiteral(expr2)
        return ExprFlexible(self, ' BETWEEN ', expr1, ' AND ', expr2)

    def not_between(self, expr1: Other, expr2: Other) -> ExprFlexible:
        """Not between."""
        if not isinstance(expr1, Expr):
            expr1 = ExprLiteral(expr1)
        if not isinstance(expr2, Expr):
            expr2 = ExprLiteral(expr2)
        return ExprFlexible(self, ' NOT BETWEEN ', expr1, ' AND ', expr2)

    def in_(self, other: Other) -> ExprBinary:
        """Compare in."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('IN', self, other)

    def not_in(self, other: Other) -> ExprBinary:
        """Compare in."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('NOT IN', self, other)

    def json_get(self, other: Other) -> ExprBinary:
        """Get json object for key."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('->', self, other)

    def json_get_value(self, other: Other) -> ExprBinary:
        """Get json value for key."""
        if not isinstance(other, Expr):
            other = ExprLiteral(other)
        return ExprBinary('->>', self, other)

    def as_(self, alias: str) -> ExprAlias:
        """Alias expression."""
        return ExprAlias(self, alias)

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        raise NotImplementedError

    __hash__ = None  # type: ignore[assignment]


class ExprAlias:
    """Expression containing aliased expression."""

    def __init__(self, expr: Expr, alias: str) -> None:
        """Initialize."""
        super().__init__()
        self.expr = expr
        self.alias = alias

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        sql, args = self.expr.__getsql__()
        return f'{sql} AS "{self.alias}"', args

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)


class ExprSubq(Expr, Generic[T]):
    """Expression containing subquery."""

    def __init__(self, value: Query[T]) -> None:
        """Initialize."""
        super().__init__()
        self.value = value

    def exists(self) -> ExprFlexible:
        """Convert to EXISTS clause."""
        return ExprFlexible('EXISTS ', self)

    def not_exists(self) -> ExprFlexible:
        """Convert to NOT EXISTS clause."""
        return ExprFlexible('NOT EXISTS ', self)

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        sql, args = self.value.__getsql__()
        return f'({sql})', args


class ExprLiteral(Expr):
    """Expression literal."""

    escapechr: str = '?'

    def __init__(
        self,
        value: SqlValue | tuple[SqlValue | Expr, ...],
        bind: bool = True,
    ) -> None:
        """Initialize expression literal."""
        super().__init__()
        self.value = value
        self.bind = bind

    def __str__(self) -> str:
        """Get string value."""
        return f'Literal: {self.value!r}'

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        value = self.value
        if value is None:
            return 'NULL', ()
        if value is True:
            return 'TRUE', ()
        if value is False:
            return 'FALSE', ()

        if isinstance(value, tuple):
            sqls = []
            args: list[BindArg] = []
            for val in value:
                if isinstance(val, Expr):
                    sql, argz = val.__getsql__()
                    sqls.append(sql)
                    args += argz
                elif self.bind:
                    sqls.append(self.escapechr)
                    args.append(val)
                else:
                    sqls.append(fmt(val))
            return f'({", ".join(sqls)})', tuple(args)

        if self.bind:
            assert not isinstance(self.value, tuple | Expr)
            return self.escapechr, (self.value,)
        return fmt(value), ()

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)


class ExprColumn(Expr):
    """Expression table column."""

    def __init__(self, schema: str | None, table: str, col: str) -> None:
        """Initialize table column expression."""
        super().__init__()
        self.schema = schema
        self.table = table
        self.col = col

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        if self.schema:
            schema = self.schema.replace('"', '""')
            schema = f'"{schema}".'
        else:
            schema = ''

        if self.table:
            table = self.table.replace('"', '""')
            table = f'"{table}".'
        else:
            table = ''

        if self.col == '*':
            col = '*'
        else:
            col = self.col.replace('"', '""')
            col = f'"{col}"'
        return f'{schema}{table}{col}', ()

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)


class ExprUnary(Expr):
    """Unary expression."""

    def __init__(self, operator: str, expr: Expr) -> None:
        """Initialize unary expression."""
        super().__init__()
        self.operator = operator
        self.expr = expr

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        expr, args = self.expr.__getsql__()
        if not isinstance(self.expr, ExprLiteral | ExprColumn):
            expr = f'({expr})'
        return f'{self.operator} {expr}', args

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)


class ExprBinary(Expr):
    """Binary expression."""

    def __init__(self, operator: str, left: Expr, right: Expr) -> None:
        """Initialize binary expression."""
        super().__init__()
        self.operator = operator
        self.left = left
        self.right = right

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        left, argsleft = self.left.__getsql__()
        right, argsright = self.right.__getsql__()
        if not isinstance(self.left, ExprLiteral | ExprColumn | ExprSubq):
            left = f'({left})'
        if not isinstance(self.right, ExprLiteral | ExprColumn | ExprSubq):
            right = f'({right})'
        return f'{left} {self.operator} {right}', (*argsleft, *argsright)

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)


class ExprFunction(Expr):
    """Expression function."""

    def __init__(self, funcname: str, *exprs: Expr) -> None:
        """Initialize function expression."""
        super().__init__()
        self.funcname = funcname
        self.exprs = exprs

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        sqls = []
        args: list[BindArg] = []
        for expr in self.exprs:
            sql, argz = expr.__getsql__()
            sqls.append(sql)
            args += argz
        return f'{self.funcname}({", ".join(sqls)})', tuple(args)

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)


class ExprFlexible(Expr):
    """Flexible expression."""

    def __init__(self, *args: str | Expr) -> None:
        """Initialize."""
        super().__init__()
        self.args = args

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Get SQL string and args."""
        res = []
        args: list[BindArg] = []
        for arg in self.args:
            if isinstance(arg, Expr):
                sql, argz = arg.__getsql__()
                args += argz
                if not isinstance(arg, ExprLiteral | ExprColumn | ExprSubq):
                    sql = f'({sql})'
                res.append(sql)
            else:
                res.append(arg)
        return ''.join(res), tuple(args)

    def typed(self, _: type[T]) -> ExprTyped[T]:
        """Convert to typed."""
        return ExprTyped[T](self)
