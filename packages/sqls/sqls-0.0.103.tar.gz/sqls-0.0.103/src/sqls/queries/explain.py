# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL EXPLAIN."""

from .query import Query


class Explain(Query):
    """EXPLAIN Query Builder."""

    def __init__(
        self,
        query_plan: bool | None = False,
    ) -> None:
        """Initialize.

        Args:
            query_plan: Get query plan.

        """
        super().__init__()
        sql = ' QUERY PLAN' if query_plan else ''
        self._parts += [f'EXPLAIN{sql} ']
