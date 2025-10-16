# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL ATTACH."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import QBase, Term

if TYPE_CHECKING:
    from .expr import Expr


class Attach(QBase[tuple[()]]):
    """ATTACH DATABASE mixin."""

    def attach(self, expr: Expr, schema: str) -> Term[tuple[()]]:
        """Create ATTACH DATABASE statement.

        Args:
            expr: Database to attach.
            schema: Schema name to attach to.

        Returns:
            Query.

        """
        esql, args = expr.__getsql__()
        schema = schema.replace('"', '""')
        sql = f'ATTACH DATABASE {esql} AS "{schema}"'
        return self._f(Term, sql, args)
