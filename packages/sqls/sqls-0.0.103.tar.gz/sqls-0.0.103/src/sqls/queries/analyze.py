# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL ANALYZE."""

from .base import QBase, Term
from .table import Table


class Analyze(QBase[tuple[()]]):
    """ANALYZE mixin."""

    def analyze(self, target: str | Table | None = None) -> Term[tuple[()]]:
        """Analyze target."""
        if target:
            if not isinstance(target, Table):
                target = Table(target)
            sql, _ = target.__getsql__()
            sql = f' {sql}'
        else:
            sql = ''
        return self._f(Term, f'ANALYZE{sql}')
