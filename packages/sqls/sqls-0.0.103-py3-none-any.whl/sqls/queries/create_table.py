# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL CREATE TABLE."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from .base import QBase, Term

if TYPE_CHECKING:
    from sqls.interfaces import SqlValue

    from .expr import Expr, ExprColumn
    from .table import Table

T1 = TypeVar('T1', bound='QBase[tuple[SqlValue, ...]]')
T2 = TypeVar('T2', bound='QBase[tuple[SqlValue, ...]]')
T3 = TypeVar('T3', bound='QBase[tuple[SqlValue, ...]]')


class CreateTable(QBase[tuple[()]]):
    """CREATE TABLE mixin."""

    def create_table(
        self,
        table: Table,
        temp: bool = False,
        if_not_exists: bool = False,
    ) -> PostCreate:
        """Start CREATE TABLE statement.

        Args:
            table: New table.
            temp: Should table be temporary.
            if_not_exists: Ignore if table exists.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()
        tmp = ' TEMP' if temp else ''
        ine = ' IF NOT EXISTS' if if_not_exists else ''
        return self._f(PostCreate, f'CREATE{tmp} TABLE{ine} {sql}', ())


class ColumnDef(QBase[tuple[()]]):
    """Column definition mixin."""

    def column(self, name: str, typ: str | None = None) -> PostColumnDef:
        """Add column definition.

        Args:
            name: Column name.
            typ: Column type.

        Returns:
            Query builder.

        """
        if self._pis(CreateTable):
            paren = ' ('
            enter = ((WithoutRowid, Term), ')')
        else:
            paren = ', '
            enter = None
        typ = f' {typ}' if typ else ''
        return self._f(PostColumnDef, f'{paren}"{name}"{typ}', enter=enter)


class ColumnConstraintGeneric(QBase[tuple[()]], Generic[T1, T2, T3]):
    """Generic column constraint mixin."""

    _next_columnconstraint: type[T1]
    _next_columnconstraint_pre: type[T2]
    _next_columnconstraint_references: type[T3]

    def primary_key(
        self,
        sort: str | None = None,
        autoincrement: bool | None = None,
    ) -> T1:
        """Add PRIMARY KEY.

        Args:
            sort: Sort order.
            autoincrement: Should add autoincrement.

        Returns:
            Query builder.

        """
        if autoincrement:
            enter = (
                (
                    ColumnDef,
                    ColumnConstraintGeneric,
                    TableConstraint,
                    WithoutRowid,
                    Term,
                ),
                ' AUTOINCREMENT',
            )
        else:
            enter = None
        sort = f' {sort}' if sort else ''
        return self._f(
            self._next_columnconstraint,
            f' PRIMARY KEY{sort}',
            enter=enter,
        )

    def not_null(self) -> T1:
        """Add NOT NULL constraint."""
        return self._f(self._next_columnconstraint, ' NOT NULL')

    def unique(self) -> T1:
        """Add UNIQUE constraint."""
        return self._f(self._next_columnconstraint, ' UNIQUE')

    def check(self, expr: Expr) -> T2:
        """Add CHECK constraint.

        Args:
            expr: Expression to check.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(self._next_columnconstraint_pre, f' CHECK ({sql})', args)

    def default(self, value: SqlValue) -> T2:
        """Add DEFAULT clause.

        Args:
            value: Default value.

        Returns:
            Query builder.

        """
        if value is None:
            return self._f(self._next_columnconstraint_pre, ' DEFAULT NULL')
        if value is True:
            return self._f(self._next_columnconstraint_pre, ' DEFAULT TRUE')
        if value is False:
            return self._f(self._next_columnconstraint_pre, ' DEFAULT FALSE')
        return self._f(self._next_columnconstraint_pre, f' DEFAULT {value!r}')

    def collate(self, name: str) -> T2:
        """Add COLLATE clause.

        Args:
            name: Collation name.

        Returns:
            Query builder.

        """
        return self._f(self._next_columnconstraint_pre, f' COLLATE {name}')

    def references(self, table: Table, *cols: ExprColumn) -> T3:
        """Add foreign-key clause.

        Args:
            table: Referenced table.
            cols: Referenced columns.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()

        def colname(col: ExprColumn) -> str:
            return f'"{col.col}"'

        return self._f(
            self._next_columnconstraint_references,
            f' REFERENCES {sql} ({", ".join(colname(x) for x in cols)})',
        )

    def generated(self, expr: Expr, stored: bool = False) -> T2:
        """Add GENERATED clause.

        Args:
            expr: Expression.
            stored: Use STORED instead of VIRTUAL.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        typ = 'STORED' if stored else 'VIRTUAL'
        return self._f(self._next_columnconstraint_pre, f' GENERATED ALWAYS AS ({sql}) {typ}', args)


class ColumnConstraint(  # yapf: prevent format
    ColumnConstraintGeneric[
        'PostColumnConstraint',
        'PostColumnDef',
        'PostColumnConstraintReferences',
    ],
):
    """Column constraint mixin."""


class OnRefchangeGeneric(QBase[tuple[()]], Generic[T1]):
    """Generic on reference change mixin."""

    _next_onrefchange: type[T1]

    def on_delete(self) -> T1:
        """Add ON DELETE action."""
        return self._f(self._next_onrefchange, ' ON DELETE')

    def on_update(self) -> T1:
        """Add ON UPDATE action."""
        return self._f(self._next_onrefchange, ' ON UPDATE')


class OnRefchange(OnRefchangeGeneric['OnRefchangeAction']):
    """On reference change mixin."""


class OnRefchangeActionGeneric(QBase[tuple[()]], Generic[T1]):
    """Generic on reference change action mixin."""

    _next_onrefchangeaction: type[T1]

    def set_null(self) -> T1:
        """Add SET NULL action."""
        return self._f(self._next_onrefchangeaction, ' SET NULL')

    def set_default(self) -> T1:
        """Add SET DEFAULT action."""
        return self._f(self._next_onrefchangeaction, ' SET DEFAULT')

    def cascade(self) -> T1:
        """Add CASCASE action."""
        return self._f(self._next_onrefchangeaction, ' CASCADE')

    def restrict(self) -> T1:
        """Add CASCASE action."""
        return self._f(self._next_onrefchangeaction, ' RESTRICT')

    def no_action(self) -> T1:
        """Add NO ACTION."""
        return self._f(self._next_onrefchangeaction, ' NO ACTION')


class OnRefchangeAction(OnRefchangeActionGeneric['PostColumnConstraintReferences']):
    """On reference change action mixin."""


class DeferrableGeneric(QBase[tuple[()]], Generic[T1]):
    """Generic deferrable mixin."""

    _next_deferrable: type[T1]

    def deferrable(self, is_deferrable: bool = True, initially: str | None = None) -> T1:
        """Add DEFERRABLE clause.

        Args:
            is_deferrable: Is column deferrable.
            initially: Initial state.

        Returns:
            Query builder.

        """
        neg = ' NOT' if not is_deferrable else ''
        initial = f' INITIALLY {initially}' if initially else ''
        return self._f(self._next_deferrable, f'{neg} DEFERRABLE{initial}')


class Deferrable(DeferrableGeneric['PostColumnDef']):
    """Deferrable mixin."""


class TableConstraint(QBase[tuple[()]]):
    """Table constraint mixin."""

    def unique_columns(self, *names: str) -> PostColumns:
        """Add UNIQUE table constraint.

        Args:
            names: Column names.

        Returns:
            Query builder.

        """
        return self._f(PostColumns, f', UNIQUE ({", ".join(names)})')

    def check_columns(self, expr: Expr) -> PostColumns:
        """Add CHECK table constraint.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostColumns, f', CHECK ({sql})', args)

    def foreign_key(self, *names: str) -> ForeignKey:
        """Start foreign-key table constraint.

        Args:
            names: Column names.

        Returns:
            Query builder.

        """
        return self._f(ForeignKey, f', FOREIGN KEY ({", ".join(names)})')


class ForeignKey(QBase[tuple[()]]):
    """Foreign key mixin."""

    def references(self, table: Table, *cols: ExprColumn) -> PostTableConstraint:
        """Add foreign-key references.

        Args:
            table: Referenced table.
            cols: Referenced columns.

        Returns:
            Query builder.

        """
        sql, _ = table.__getsql__()

        def colname(col: ExprColumn) -> str:
            return f'"{col.col}"'

        return self._f(
            PostTableConstraint,
            f' REFERENCES {sql} ({", ".join(colname(x) for x in cols)})',
        )


class OnConflictGeneric(QBase[tuple[()]], Generic[T1]):
    """Generic on conflict mixin."""

    _next_conflictclause: type[T1]

    def _on_conflict(self, term: str) -> T1:
        """Add ON CONFLICT clause.

        Args:
            term: Action to take.

        Returns:
            Query builder.

        """
        return self._f(self._next_conflictclause, f' ON CONFLICT {term}')

    def on_conflict_rollback(self) -> T1:
        """Add ON CONFLICT ROLLBACK."""
        return self._on_conflict('ROLLBACK')

    def on_conflict_abort(self) -> T1:
        """Add ON CONFLICT ABORT."""
        return self._on_conflict('ABORT')

    def on_conflict_fail(self) -> T1:
        """Add ON CONFLICT FAIL."""
        return self._on_conflict('FAIL')

    def on_conflict_ignore(self) -> T1:
        """Add ON CONFLICT IGNORE."""
        return self._on_conflict('IGNORE')

    def on_conflict_replace(self) -> T1:
        """Add ON CONFLICT REPLACE."""
        return self._on_conflict('REPLACE')


class OnConflict(OnConflictGeneric['PostConflict']):
    """On conflict mixin."""


class OnRefchangeTbl(OnRefchangeGeneric['OnRefchangeTblAction']):
    """On reference change table mixin."""


class OnRefchangeTblAction(OnRefchangeActionGeneric['PostTableConstraint']):
    """On reference change action table mixing."""


class DeferrableTbl(DeferrableGeneric['PostColumns']):
    """Deferrable table mixin."""


class WithoutRowid(QBase[tuple[()]]):
    """WITHOUT ROWID mixin."""

    def without_rowid(self) -> Term[tuple[()]]:
        """Enable WITHOUT ROWID."""
        return self._f(Term, ' WITHOUT ROWID')


class PostCreate(
    ColumnDef,
):
    """Post create builder."""


class PostColumnDef(
    ColumnDef,
    ColumnConstraint,
    TableConstraint,
    WithoutRowid,
    Term[tuple[()]],
):
    """Post column definition builder."""


class PostColumnConstraint(
    PostColumnDef,
    OnConflict,
):
    """Post column constraint builder."""


class PostColumnConstraintReferences(
    PostColumnDef,
    OnRefchange,
    Deferrable,
):
    """Post column constraint references builder."""


class PostConflict(
    PostColumnDef,
):
    """Post conflict builder."""


class PostColumns(
    TableConstraint,
    WithoutRowid,
    Term[tuple[()]],
):
    """Post columns builder."""


class PostTableConstraint(
    PostColumns,
    OnRefchangeTbl,
    DeferrableTbl,
):
    """Post table constraint builder."""
