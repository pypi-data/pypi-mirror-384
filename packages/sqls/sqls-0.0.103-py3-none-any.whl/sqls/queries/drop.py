# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL CREATE DROP."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from .table import Table


class Drop(QBase[tuple[()]]):
    """DROP mixin."""

    def drop_index(self, index: Table, if_exists: bool = False) -> PostDrop:
        """Create DROP INDEX statement.

        Args:
            index: Index to drop.
            if_exists: Execute statement only if index exists.

        Returns:
            Query.

        """
        sql, _ = index.__getsql__()
        ife = ' IF EXISTS' if if_exists else ''
        return self._f(PostDrop, f'DROP INDEX{ife} {sql}')

    def drop_table(self, table: Table, if_exists: bool = False) -> PostDrop:
        """Create DROP TABLE statement.

        Args:
            table: Table to drop.
            if_exists: Execute statement only if table exists.

        Returns:
            Query.

        """
        sql, _ = table.__getsql__()
        ife = ' IF EXISTS' if if_exists else ''
        return self._f(PostDrop, f'DROP TABLE{ife} {sql}')

    def drop_trigger(self, trigger: Table, if_exists: bool = False) -> PostDrop:
        """Create DROP TRIGGER statement.

        Args:
            trigger: Trigger to drop.
            if_exists: Execute statement only if trigger exists.

        Returns:
            Query.

        """
        sql, _ = trigger.__getsql__()
        ife = ' IF EXISTS' if if_exists else ''
        return self._f(PostDrop, f'DROP TRIGGER{ife} {sql}')

    def drop_view(self, view: Table, if_exists: bool = False) -> PostDrop:
        """Create DROP VIEW statement.

        Args:
            view: Viewt o drop.
            if_exists: Execute statement only if view exists.

        Returns:
            Query.

        """
        sql, _ = view.__getsql__()
        ife = ' IF EXISTS' if if_exists else ''
        return self._f(PostDrop, f'DROP VIEW{ife} {sql}')


class PostDrop(
    Term[tuple[()]],
):
    """Post drop builder."""
