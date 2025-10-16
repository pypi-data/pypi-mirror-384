# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Database connection and transaction management."""

from .exceptions import IntegrityError, OperationalError
from .manager import get_manager

__all__ = [
    'IntegrityError',
    'OperationalError',
    'get_manager',
]
