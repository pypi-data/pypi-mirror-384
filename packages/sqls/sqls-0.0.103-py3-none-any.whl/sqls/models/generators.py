# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Model query generators."""

from __future__ import annotations

from dataclasses import fields
from itertools import combinations
from types import NoneType
from typing import TYPE_CHECKING, Annotated, Union, get_args, get_origin, get_type_hints

from sqls.queries import Query, Table

from .model import Fieldmeta, Model

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TypeVar

    from sqls.interfaces import Query as QueryProtocol

    T = TypeVar('T')

SQLITE_TYPEMAP = {
    'AutoField': 'INTEGER',
    'BigAutoField': 'INTEGER',
    'IntegerField': 'INTEGER',
    'BigIntegerField': 'INTEGER',
    'SmallIntegerField': 'INTEGER',
    'FloatField': 'REAL',
    'DoubleField': 'REAL',
    'DecimalField': 'DECIMAL',
    'CharField': 'VARCHAR',
    'FixedCharField': 'CHAR',
    'TextField': 'TEXT',
    'BlobField': 'BLOB',
    'UUIDField': 'TEXT',
    'DateTimeField': 'DATETIME',
    'DateField': 'DATE',
    'TimeField': 'TIME',
    'BooleanField': 'INTEGER',
    'ForeignKeyField': 'INTEGER',
}


def get_create_queries(  # noqa: C901, PLR0912, PLR0915
    models: Sequence[type[Model]],
) -> list[QueryProtocol[tuple[()]]]:
    """Get create table queries for models."""
    query: QueryProtocol[tuple[()]]
    queries: list[QueryProtocol[tuple[()]]] = []
    idxqueries: list[QueryProtocol[tuple[()]]] = []

    byname = {model.__model__['name']: model for model in models}

    for name, model in byname.items():
        tablemeta = model.__tablemeta__
        modelmeta = model.__model__
        table = Table(tablemeta.name or name, tablemeta.schema)

        query = Query().create_table(table, if_not_exists=True)

        hints = get_type_hints(model, include_extras=True)
        haspk = False
        for sub in fields(model):
            if sub.name == 'id' and model.__noid__:
                continue

            nullable = False
            fieldmeta = Fieldmeta()
            hint = hints[sub.name]
            assert hint is not NoneType

            if get_origin(hint) is Union:
                assert get_args(hint)[1] is NoneType
                nullable = True
                hint = get_args(hint)[0]

            assert get_origin(hint) == Annotated
            hint, *hintargs = get_args(hint)
            argtype = hintargs[0]
            if len(hintargs) == 2:
                fieldmeta = hintargs[1]

            suffix = f'({fieldmeta.max_length})' if fieldmeta.max_length is not None else ''
            query = query.column(sub.name, f'{SQLITE_TYPEMAP[argtype]}{suffix}')
            if sub.name == 'id':
                query = query.primary_key(autoincrement=True)
                haspk = True
            if not nullable:
                query = query.not_null()
            if fieldmeta.unique:
                query = query.unique()
            if fieldmeta.default is not None:
                query = query.default(fieldmeta.default)
            if argtype == 'ForeignKeyField':
                if fieldmeta.foreign_key:
                    foreign_key = fieldmeta.foreign_key
                else:
                    assert sub.name.endswith('_id')
                    foreign_key = (sub.name[:-3], 'id')
                modelmeta['temp_rels'].append((haspk, *foreign_key, sub.name))
                other = Table(foreign_key[0])
                query = query.references(other, getattr(other, foreign_key[1]))
                if fieldmeta.on_delete == 'RESTRICT':
                    query = query.on_delete().restrict()
                elif fieldmeta.on_delete == 'SET DEFAULT':
                    query = query.on_delete().set_default()
                elif fieldmeta.on_delete == 'SET NULL':
                    query = query.on_delete().set_null()
                else:
                    query = query.on_delete().cascade()
                if sub.name != 'id':
                    idxtable = Table(f'idx__{name}__{sub.name}')
                    idxqueries.append(
                        Query().create_index(
                            idxtable,
                            table,
                            getattr(table, sub.name),
                            if_not_exists=True,
                        ),
                    )

        queries.append(query)

        for indexmeta in tablemeta.indexes:
            idxtable = Table(f'idx__{name}__{"__".join(indexmeta.fields)}')
            idxqueries.append(
                Query().create_index(
                    idxtable,
                    table,
                    *[getattr(table, x) for x in indexmeta.fields],
                    unique=indexmeta.unique,
                    if_not_exists=True,
                ),
            )

    for model in models:
        model.__model__['forward_rels'].clear()
        model.__model__['backward_rels'].clear()
        model.__model__['through_rels'].clear()

    for model in models:
        modelmeta = model.__model__
        indirects = []
        for direct, othername, backfield, fwdfield in modelmeta['temp_rels']:
            if direct:
                othermodel = byname[othername]

                model.__model__['forward_rels'].append((othermodel, backfield, fwdfield))
                othermodel.__model__['backward_rels'].append((model, fwdfield, backfield))
            else:
                indirects.append((othername, backfield, fwdfield))

        for left, right in combinations(indirects, 2):
            leftmodel = byname[left[0]]
            rightmodel = byname[right[0]]
            leftmodel.__model__['through_rels'].append(
                (model, left[2], left[1], rightmodel, *right[1:]),
            )
            rightmodel.__model__['through_rels'].append(
                (model, right[2], right[1], leftmodel, *left[1:]),
            )

        modelmeta['temp_rels'].clear()

    return queries + idxqueries
