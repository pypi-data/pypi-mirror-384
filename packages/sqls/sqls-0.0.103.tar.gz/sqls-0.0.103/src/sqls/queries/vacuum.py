# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL VACUUM."""

from .base import QBase, Term
from .expr import Expr, ExprLiteral


class Vacuum(QBase[tuple[()]]):
    """VACUUM mixin."""

    def vacuum(self, schema: str | None = None, into: Expr | str | None = None) -> Term[tuple[()]]:
        """Create VACUUM statement.

        Args:
            schema: Schema to run on or all.
            into: Target database to vacuum into.

        Returns:
            Query.

        """
        if schema:
            schema = schema.replace('"', '""')
            schema = f' "{schema}"'
        else:
            schema = ''

        if into:
            if not isinstance(into, Expr):
                into = ExprLiteral(into)
            sql, args = into.__getsql__()
            sql = f' INTO {sql}'
        else:
            sql = ''
            args = ()

        sql = f'VACUUM{schema}{sql}'
        return self._f(Term, sql, args)
