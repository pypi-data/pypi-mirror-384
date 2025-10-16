# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL REINDEX."""

from .base import QBase, Term
from .table import Table


class Reindex(QBase[tuple[()]]):
    """REINDEX mixin."""

    def reindex(self, target: str | Table | None = None) -> Term[tuple[()]]:
        """Create REINDEX statement.

        Args:
            target: Reindexing target.

        Returns:
            Query.

        """
        if target:
            if not isinstance(target, Table):
                target = Table(target)
            sql, _ = target.__getsql__()
            sql = f' {sql}'
        else:
            sql = ''
        return self._f(Term, f'REINDEX{sql}')
