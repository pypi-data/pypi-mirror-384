# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""SQL Query."""

from .alter import Alter
from .analyze import Analyze
from .attach import Attach
from .create_index import CreateIndex
from .create_table import CreateTable
from .create_trigger import CreateTrigger
from .create_view import CreateView
from .delete import Delete
from .detach import Detach
from .drop import Drop
from .insert import Insert
from .pragma import Pragma
from .reindex import Reindex
from .select import Select
from .update import Update
from .vacuum import Vacuum
from .withq import With


class Query(
    Alter,
    Analyze,
    Attach,
    CreateIndex,
    CreateTable,
    CreateTrigger,
    CreateView,
    Delete,
    Detach,
    Drop,
    Insert,
    Pragma,
    Reindex,
    Select,
    Update,
    Vacuum,
    With,
):
    """SQL Query Builder.

    All regular SQL queries are build up from here.

    """
