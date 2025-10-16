# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL CREATE VIEW."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from .base import Texplicit
    from .expr import ExprColumn
    from .table import Table


class CreateView(QBase[tuple[()]]):
    """CREATE VIEW mixin."""

    def create_view(
        self,
        view: Table,
        temp: bool = False,
        if_not_exists: bool = False,
    ) -> PostCreate:
        """Start CREATE VIEW statement.

        Args:
            view: Table to create.
            temp: Is view temporary.
            if_not_exists: Ignore existing view.

        Returns:
            Query builder.

        """
        sql, _ = view.__getsql__()
        tmp = ' TEMP' if temp else ''
        ine = ' IF NOT EXISTS' if if_not_exists else ''
        sql = f'CREATE{tmp} VIEW{ine} {sql}'
        return self._f(PostCreate, sql)


class Columns(QBase[tuple[()]]):
    """Columns mixin."""

    def columns(self, *cols: ExprColumn) -> PostColumns:
        """Add columns.

        Args:
            cols: Columns.

        Returns:
            Query builder.

        """
        return self._f(PostColumns, f'({", ".join(x.col for x in cols)})')


class As(QBase[tuple[()]]):
    """AS mixin."""

    def as_(self, select: QBase[Texplicit]) -> PostAs:
        """Add AS clause.

        Args:
            select: Select statement.

        Returns:
            Query builder.

        """
        sql, args = select.__getsql__()
        return self._f(PostAs, f' AS {sql}', args)


class PostCreate(
    Columns,
    As,
):
    """Post create builder."""


class PostColumns(
    As,
):
    """Post columns builder."""


class PostAs(
    Term[tuple[()]],
):
    """Post AS builder."""
