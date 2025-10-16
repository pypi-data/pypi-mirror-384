# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL PRAGMA."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from sqls.interfaces import SqlValue


class Pragma(QBase[tuple[()]]):
    """PRAGMA mixin."""

    def pragma(
        self,
        pragma: str,
        schema: str | None = None,
        value: str | float | None = None,  # | int
    ) -> Term[tuple[SqlValue, ...]]:
        """Create PRAGMA statement.

        Args:
            pragma: Pragma name or function with value.
            schema: Schema name.
            value: Value to set.

        Returns:
            Query.

        """
        if schema:
            schema = schema.replace('"', '""')
            schema = f'"{schema}".'
        else:
            schema = ''

        value = f' = {value!r}' if value else ''

        pragma = pragma.replace('"', '""')
        return self._f(Term, f'PRAGMA {schema}"{pragma}"{value}')
