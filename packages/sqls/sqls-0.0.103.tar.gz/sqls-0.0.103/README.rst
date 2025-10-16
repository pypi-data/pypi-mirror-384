.. image:: https://img.shields.io/pypi/v/sqls
   :alt: version

.. image:: https://img.shields.io/pypi/l/sqls
   :alt: license

.. image:: https://img.shields.io/pypi/pyversions/sqls
   :alt: python versions

.. image:: https://gitlab.com/durko/sqls/badges/master/pipeline.svg
   :target: https://gitlab.com/durko/sqls/-/commits/master
   :alt: pipeline status

.. image:: https://gitlab.com/durko/sqls/badges/master/coverage.svg
   :target: https://gitlab.com/durko/sqls/-/commits/master
   :alt: coverage report


====
SQLs
====

SQLs is a collection of libraries to interact with SQL databases. SQLs is not an object-relational mapper (ORM), but offers useful low-level primitives for handling transactions, defining a data model, and formulating queries in Python. Its main design goal is helping developers write SQL in idiomatic, type-checked Python, while being fast and efficient on runtime.


Getting started
===============

For more, see the `documentation <https://durko.gitlab.io/sqls/>`_.

SQLs is published on PyPI and does not have any special dependencies. Simply install with pip::

   pip install sqls

Dependencies on database interface libraries are strictly optional. If you want to speak to a specific SQL implementation use any of::

   pip install sqls[mysql]
   pip install sqls[postgresql]
   pip install sqls[sqlite]
   pip install sqls[mysql,postgre,sqlite]


Connect to a database
=====================

Asynchronous transaction managers from ``sqls.transactions`` handle SQL database connections:

.. code-block:: python

   from sqls.transactions import get_manager

   async def application() -> list[tuple[int]]:
       # Create a transaction manager.
       manager = get_manager('file:///path/to/sqlite.db')

       # Initialize database connections.
       await manager.init()

       # Open transaction.
       async with manager.txn() as txn:

          # Execute query.
          return await txn.execute('SELECT 1')

       # Close database connections.
       await manager.close()


All SQL statements inside the asynchronous context manager are executed in one single transaction. Uncaught exceptions in the context will cause the transaction to be automatically rolled back, on regular exit the transaction will automatically be committed.


Define a data model
===================

The data model is defined through annotated Python dataclasses and the ``Model`` base class from ``sqls.models``.

Basic usage
-----------

The syntax uses builtin Python primitives to express the rich details of SQL types:

.. code-block:: python

   from dataclasses import dataclass
   from typing import Annotated

   from sqls.models import CharField, Fieldmeta, IntegerField, Model

   @dataclass
   class User(Model):
       """A user model."""

       # Names are unique.
       name: Annotated[CharField, Fieldmeta(max_length=32, unique=True)]

       # Passwords are nullable.
       password: Annotated[CharField, Fieldmeta(max_length=128)] | None

       # Use just a plain integer.
       time_created: IntegerField

The Model base class automatically adds an integer primary key ``id`` field.

Relationships
-------------

Relationships are expressed through annotations on fields that store the actual information:

.. code-block:: python

   @dataclass
   class User(Model):
       """Same as above, add some relationships."""

       # Table name and field are inferred from the attribute name.
       company_id: ForeignKeyField

       # Table name and field are explicitly set though Fieldmeta.
       team_id: Annotated[ForeignKeyField, Fieldmeta(foreign_key=('department', 'id'))

Many-to-many relationships cannot be expressed on the related models themselves, the table needs to be defined explicitly:

.. code-block:: python

   @dataclass
   class UserGroup(Model):
       """User group relationship."""

       # Disable automatic injection of id field.
       id: None
       user_id: ForeignKeyField
       group_id: ForeignKeyField


Create database tables
======================

The ``sqls.models`` package can generate ``CREATE TABLE`` queries from model definitions:

.. code-block:: python

   from sqls.models import get_create_queries

   # Inside a transaction context (txn) create tables for User and Group.
   for query in get_create_queries([User, UserGroup, Group]):
       # Execute generated query with txn.exq.
       await txn.exq(query)


Build queries
=============

The ``sqls.queries`` package helps writing queries in idiomatic python:

.. code-block:: python

   from sqls.queries import Query, Table

   # Create Table object from sql table name.
   user_t = Table('user')

   # Create query for id and password of one specific user.
   query = (
       Query
       .select(
           user_t.id.typed(int),
           user_t.password.typed(str | None),
        )
       .from_(user_t)
       .where(user_t.name == 'Ringo')
   )

As SQLs is not an ORM, ``Query`` knows nothing about the data model. By expressing the expected return type of the id field with ``.typed(int)`` static typed checkers like `mypy <https://mypy-lang.org/>`_ are able to infer the return types when the query is executed.

Development
===========

Clone the repository and setup your local checkout::

   git clone https://gitlab.com/durko/sqls.git

   cd sqls
   python -m venv venv
   . venv/bin/activate

   pip install -r requirements-dev.txt
   pip install -e .


This creates a new virtual environment with the necessary python dependencies and installs SQLs in editable mode. The SQLs code base uses pytest as its test runner, run the test suite by simply invoking::

   pytest


To build the documentation from its source run sphinx-build::

   sphinx-build -a docs build/public


The entry point to the local documentation build should be available under ``build/public/index.html``.
