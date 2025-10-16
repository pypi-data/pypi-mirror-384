# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Model field types."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Annotated

AutoField = Annotated[int, 'AutoField']
BigAutoField = Annotated[int, 'BigAutoField']
IntegerField = Annotated[int, 'IntegerField']
BigIntegerField = Annotated[int, 'BigIntegerField']
SmallIntegerField = Annotated[int, 'SmallIntegerField']
FloatField = Annotated[float, 'FloatField']
DoubleField = Annotated[float, 'DoubleField']
DecimalField = Annotated[float, 'DecimalField']  # max_digits, decimals
CharField = Annotated[str, 'CharField']  # max_length
FixedCharField = Annotated[str, 'FixedCharField']  # length
TextField = Annotated[str, 'TextField']
BlobField = Annotated[bytes, 'BlobField']
UUIDField = Annotated[str, 'UUIDField']
DateTimeField = Annotated[datetime, 'DateTimeField']
DateField = Annotated[date, 'DateField']
TimeField = Annotated[time, 'TimeField']
BooleanField = Annotated[bool, 'BooleanField']
ForeignKeyField = Annotated[int, 'ForeignKeyField']  # model, on_delete
