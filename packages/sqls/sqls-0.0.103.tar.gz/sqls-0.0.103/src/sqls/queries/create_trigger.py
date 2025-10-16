# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL CREATE TRIGGER."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from sqls.interfaces import BindArg

    from .expr import Expr, ExprColumn
    from .table import Table


class CreateTrigger(QBase[tuple[()]]):
    """CREATE TRIGGER mixin."""

    def create_trigger(
        self,
        trigger: Table,
        temp: bool = False,
        if_not_exists: bool = False,
    ) -> PostCreate:
        """Start CREATE TRIGGER statement.

        Args:
            trigger: Table.
            temp: Is trigger temporary.
            if_not_exists: Ignore if trigger exists.

        Returns:
            Query builder.

        """
        sql, _ = trigger.__getsql__()
        tmp = ' TEMP' if temp else ''
        ine = ' IF NOT EXISTS' if if_not_exists else ''
        sql = f'CREATE{tmp} TRIGGER{ine} {sql}'
        return self._f(PostCreate, sql)


class Moment(QBase[tuple[()]]):
    """Moment mixin."""

    def before(self) -> PostMoment:
        """Add BEFORE keyword."""
        return self._f(PostMoment, ' BEFORE')

    def after(self) -> PostMoment:
        """Add AFTER keyword."""
        return self._f(PostMoment, ' AFTER')

    def instead_of(self) -> PostMoment:
        """Add INSTEAD OF keyword."""
        return self._f(PostMoment, ' INSTEAD OF')


class Cause(QBase[tuple[()]]):
    """Cause mixin."""

    def delete(self) -> PostCause:
        """Add DELETE keyword."""
        return self._f(PostCause, ' DELETE')

    def insert(self) -> PostCause:
        """Add INSERT keyword."""
        return self._f(PostCause, ' INSERT')

    def update(self, of_: list[ExprColumn] | None = None) -> PostCause:
        """Add UPDATE OF keyword.

        Args:
            of_: List of columns.

        Returns:
            Query builder.

        """
        sql = f' OF {", ".join(x.col for x in of_)}' if of_ else ''
        return self._f(PostCause, f' UPDATE{sql}')


class On(QBase[tuple[()]]):
    """ON mixin."""

    def on_(self, table: Table) -> PostOn:
        """Add ON clause.

        Args:
            table: Table to trigger on.

        Returns:
            Query builder.

        """
        sql, args = table.__getsql__()
        return self._f(PostOn, f' ON {sql}', args)


class Foreach(QBase[tuple[()]]):
    """FOR EACH ROW mixin."""

    def for_each_row(self) -> PostForeach:
        """FOR EACH ROW clause."""
        return self._f(PostForeach, ' FOR EACH ROW')


class When(QBase[tuple[()]]):
    """WHEN mixin."""

    def when(self, expr: Expr) -> PostWhen:
        """Add WHEN clause.

        Args:
            expr: Expression.

        Returns:
            Query builder.

        """
        sql, args = expr.__getsql__()
        return self._f(PostWhen, f' WHEN {sql}', args)


class Statements(QBase[tuple[()]]):
    """Trigger statements mixin."""

    def statements(self, *statements: QBase[tuple[()]]) -> PostStatements:
        """Add trigger statements.

        Args:
            statements: Queries to run in trigger.

        Returns:
            Query.

        """
        sqls = []
        args: list[BindArg] = []
        for statement in statements:
            sql, argz = statement.__getsql__()
            sqls.append(f'{sql};')
            args += argz
        return self._f(PostStatements, f' BEGIN {" ".join(sqls)} END', tuple(args))


class PostCreate(
    Moment,
    Cause,
):
    """Post create builder."""


class PostMoment(
    Cause,
):
    """Post moment builder."""


class PostCause(
    On,
):
    """Post cause builder."""


class PostOn(
    Foreach,
    When,
    Statements,
):
    """Post on builder."""


class PostForeach(
    When,
    Statements,
):
    """Post for each builder."""


class PostWhen(
    Statements,
):
    """Post when builder."""


class PostStatements(
    Term[tuple[()]],
):
    """Post statements builder."""
