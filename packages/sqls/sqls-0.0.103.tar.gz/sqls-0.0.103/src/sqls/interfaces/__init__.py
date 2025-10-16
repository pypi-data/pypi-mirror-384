# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQLS interface definitions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, TypeAlias, TypedDict, TypeVar

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

SqlValue: TypeAlias = bool | bytes | float | int | str | None
BindArg: TypeAlias = SqlValue | Sequence[SqlValue]

T = TypeVar('T')


class ManagerOptions(TypedDict, total=False):
    """Manager options."""

    max_connections: int
    init_pragmas: Sequence[str]
    fini_pragmas: Sequence[str]


class SupportsGetsql(Protocol):
    """Query Protocol."""

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:  # pragma: no cover
        """Get query string."""
        raise NotImplementedError


class Query(SupportsGetsql, Protocol[T]):
    """Query Protocol."""

    attr: T | None


class Transaction(Protocol):
    """Transaction."""

    async def execute(
        self,
        query: str,
        *args: BindArg,
    ) -> list[tuple[SqlValue, ...]]:  # pragma: no cover
        """Just execute."""
        raise NotImplementedError

    async def exq(self, query: Query[T]) -> list[T]:  # pragma: no cover
        """Execute shorthand."""
        raise NotImplementedError

    async def exq_count(self, query: SupportsGetsql) -> int:  # pragma: no cover
        """Execute shorthand."""
        raise NotImplementedError


class Manager(Protocol):
    """Database manager."""

    def __init__(
        self,
        uri: str,
        options: ManagerOptions | None = None,
    ) -> None:  # pragma: no cover
        """Initialize."""
        raise NotImplementedError

    async def init(self) -> None:  # pragma: no cover
        """Initialize database connections."""
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover
        """Close all database connections."""
        raise NotImplementedError

    def txn(
        self,
        immediate: bool = False,
    ) -> AbstractAsyncContextManager[Transaction]:  # pragma: no cover
        """Open a transaction for database operations."""
        raise NotImplementedError
