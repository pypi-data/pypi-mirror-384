# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Query base."""

from __future__ import annotations

import sys
from collections.abc import Callable  # noqa: TC003
from functools import wraps
from typing import (
    TYPE_CHECKING,
    ClassVar,
    ForwardRef,
    Generic,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from sqls.interfaces import BindArg, SqlValue

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Concatenate, ParamSpec, TypeAlias

    P = ParamSpec('P')
    R = TypeVar('R')

    Other = TypeVar('Other', bound='QBase[Texplicit]')

Texplicit: TypeAlias = tuple[SqlValue | object, ...]
T_co = TypeVar('T_co', bound='Texplicit', covariant=True)


def get_generics(cls: type[QBase[T_co]]) -> Generator[type[QBase[Texplicit]], None, None]:
    """Get generic parents."""
    for parent in getattr(cls, '__orig_bases__', []):
        origin = get_origin(parent)
        if not origin or not issubclass(origin, QBase):
            continue
        yield parent
        yield from get_generics(origin)


class QBase(Generic[T_co]):
    """Base for queries."""

    _unfinished: ClassVar[dict[tuple[str, str], list[type[QBase[Texplicit]]]]] = {}

    _parts: list[str]
    _args: list[BindArg]
    _enterstack: list[tuple[tuple[type[QBase[Texplicit]], ...], str]]

    endq: Callable[[], Term[T_co]]

    attr: T_co | None = None

    def __init__(self, parent: QBase[Texplicit] | None = None) -> None:
        """Initialize."""
        super().__init__()
        self._parent: QBase[Texplicit] | None
        if parent:
            self._parts = parent._parts[:]  # noqa: SLF001
            self._args = parent._args[:]  # noqa: SLF001
            self._enterstack = parent._enterstack[:]  # noqa: SLF001
            self._parent = parent
        else:
            self._parts = []
            self._args = []
            self._enterstack = []
            self._parent = None
        self._calledon: type | None = None

    def _append(self, other: QBase[Texplicit]) -> None:
        """Forward own state to other."""
        assert not self._enterstack
        self._parts += other._parts
        self._args += other._args

    def _pis(self, *classes: type) -> bool:
        """Check if parent is instance of class."""
        assert self._parent
        return self._parent._calledon in classes  # noqa: SLF001

    def _f(
        self,
        cls: type[Other],
        parts: str,
        args: tuple[BindArg, ...] = (),
        enter: tuple[tuple[type[QBase[Texplicit]], ...], str] | None = None,
    ) -> Other:
        """Forward self and args to next."""
        inst = cls(cast('QBase[tuple[SqlValue, ...]]', self))
        inst._parts += [parts]
        inst._args += args
        if enter:
            inst._enterstack.append(enter)
        return inst

    def __str__(self) -> str:
        """Generate querystring."""
        lastpart = '' if isinstance(self, Term) else ' #INCOMPLETE#'
        return ''.join([*self._parts, lastpart])

    def __getsql__(self) -> tuple[str, tuple[BindArg, ...]]:
        """Shorthand for str."""
        if self._calledon != Term:
            return self.endq().__getsql__()

        assert not self._enterstack, 'Enterstack should be empty'
        return str(self), tuple(self._args)

    @classmethod
    def _getfn(
        cls: type[QBase[T_co]],
        attr: Callable[Concatenate[QBase[T_co], P], R],
    ) -> Callable[Concatenate[QBase[T_co], P], R]:
        def func(obj: QBase[T_co], /, *args: P.args, **kwargs: P.kwargs) -> R:
            stack = obj._enterstack
            while stack:
                classes, callback = stack[-1]
                if cls not in classes:
                    break
                stack.pop()
                obj._parts += [callback]
            obj._calledon = cls
            return attr(obj, *args, **kwargs)

        return func

    @classmethod
    def __init_generics__(cls: type[QBase[T_co]]) -> None:
        """Set _next members."""
        module = sys.modules[cls.__module__].__dict__
        module.update({cls.__name__: cls, 'Type': type})
        try:
            for parent in get_generics(cls):
                origin = get_origin(parent)
                varmap = dict(
                    zip(
                        [
                            x
                            for base in getattr(origin, '__orig_bases__', [])
                            if get_origin(base) is Generic
                            for x in base.__parameters__
                        ],
                        get_args(parent),
                        strict=False,
                    ),
                )
                for key in [x for x in origin.__annotations__ if x.startswith('_next')]:
                    hints = get_type_hints(origin)
                    arg = get_args(hints[key])[0]
                    fref = varmap.get(arg, arg)

                    assert isinstance(fref, ForwardRef)
                    if sys.version_info >= (3, 14):
                        evald = fref.evaluate(locals=module)
                    elif sys.version_info >= (3, 12):  # pragma: no cover
                        evald = fref._evaluate(  # noqa: SLF001
                            module,
                            module,
                            type_params=(),
                            recursive_guard=frozenset(),
                        )
                    else:  # pragma: no cover
                        evald = fref._evaluate(  # noqa: SLF001
                            module,
                            module,
                            recursive_guard=frozenset(),
                        )
                    setattr(cls, key, evald)
        except NameError as err:
            name = str(err).split("'")[1]
            name = '' if name == cls.__name__ else name
            cls._unfinished.setdefault(
                (cls.__module__, name),
                [],
            ).append(cast('type[QBase[Texplicit]]', cls))
            return

        for unfikey in [(cls.__module__, cls.__name__), (cls.__module__, '')]:
            if unfikey in cls._unfinished:
                insts = cls._unfinished.pop(unfikey)
                for inst in insts:
                    inst.__init_generics__()

    def __init_subclass__(cls) -> None:
        """Add calledon wrapper."""
        super().__init_subclass__()
        for name in cls.__dict__:
            if name[0] == '_':
                continue
            attr = getattr(cls, name)
            assert callable(attr)
            setattr(cls, name, wraps(attr)(cls._getfn(attr)))
        cls.__init_generics__()


class Term(QBase[T_co]):
    """Noop."""

    def endq(self) -> Term[T_co]:
        """Done."""
        return self
