# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Transaction manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqls.interfaces import Manager, ManagerOptions


def get_manager(uri: str, options: ManagerOptions | None = None) -> Manager:
    """Get manager instance for URI."""
    if uri.startswith('mysql:'):
        from .mysql import Manager as MysqlManager

        return MysqlManager(uri, options)
    if uri.startswith('postgresql:'):
        from .postgresql import Manager as PostgresqlManager

        return PostgresqlManager(uri, options)
    assert uri.startswith(('sqlite:', 'file:', ':memory:'))
    from .sqlite import Manager as SqliteManager

    return SqliteManager(uri, options)
