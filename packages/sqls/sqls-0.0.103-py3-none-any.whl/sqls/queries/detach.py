# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL DETACH."""

from .base import QBase, Term


class Detach(QBase[tuple[()]]):
    """DETACH DATABASE mixin."""

    def detach(self, schema: str) -> Term[tuple[()]]:
        """Create DETACH DATABASE statement.

        Args:
            schema: Schema name to detach.

        Returns:
            Query.

        """
        schema = schema.replace('"', '""')
        sql = f'DETACH DATABASE "{schema}"'
        return self._f(Term, sql)
