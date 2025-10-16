# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Model base class and utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NamedTuple, TypedDict

from .fields import AutoField  # noqa: TC001

if TYPE_CHECKING:
    from typing import TypeVar

    from sqls.interfaces import SqlValue

    T = TypeVar('T')

RE_SNAKE = re.compile(r'(?<!^)(?=[A-Z])')


class Indexmeta(NamedTuple):
    """Index metadata."""

    fields: tuple[str, ...]
    unique: bool = False


class Tablemeta(NamedTuple):
    """Table configuration."""

    schema: str | None = None
    name: str | None = None
    indexes: tuple[Indexmeta, ...] = ()


class Fieldmeta(NamedTuple):
    """Field configuration."""

    name: str | None = None
    primary: bool = False
    unique: bool = False
    collation: str | None = None
    default: SqlValue = None
    foreign_key: tuple[str, str] | None = None
    max_length: int | None = None
    on_delete: str | None = None


class Metadata(TypedDict):
    """Model metadata."""

    name: str
    temp_rels: list[tuple[bool, str, str, str]]
    forward_rels: list[tuple[type[Model], str, str]]
    backward_rels: list[tuple[type[Model], str, str]]
    through_rels: list[tuple[type[Model], str, str, type[Model], str, str]]


@dataclass
class Model:
    """Model mixin."""

    __noid__: ClassVar[bool] = False
    __tablemeta__: ClassVar[Tablemeta] = Tablemeta()
    __model__: ClassVar[Metadata]  # = {}

    id: AutoField

    def __init_subclass__(cls) -> None:
        """Initialize __model__ attribute."""
        cls.__model__ = {
            'name': RE_SNAKE.sub('_', cls.__name__).lower(),
            'temp_rels': [],
            'forward_rels': [],
            'backward_rels': [],
            'through_rels': [],
        }
