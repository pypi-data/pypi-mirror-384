# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Transactions test tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from sqls.interfaces import BindArg

T = TypeVar('T')


class Query(Generic[T]):
    """Query helper."""

    attr: T

    def __init__(self, query: str, *args: BindArg) -> None:
        """Initialize."""
        self.query = query
        self.args = args

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Retrieve query string."""
        return self.query, self.args
