Models
======

In :py:mod:`sqls.models` SQLs provides tools to create a data model and generate queries to create tables and indices for the model.


Define a model
--------------

The syntax is built on standard Python dataclasses and the :py:class:`Model <sqls.models.Model>` base class.

Example:

.. code-block:: python

   from dataclasses import dataclass
   from typing import Annotated

   from sqls.models import TextField, IntegerField

   @dataclass
   class Player(Model):
       """A player model."""

       nickname: TextField
       highscore: IntegerField

The dataclass itself will corresponds to a table, and each dataclass field corresponds to a table column. The field name will be mapped to the column name, the column type will be derived from the Python field type.

The ``Model`` base class automatically injects an integer field called ``id`` for the primary key. If ``id`` is set to another type in a model definition, this type will be used instead. A type of ``None`` will deactivate the automatic primary key insertion.


Configuring fields
------------------

SQL columns have more properties than just the value type. In SQLs this metadata can be expressed through annotated types. The only exception is the `nullability` property, as this also affects how the type behaves in Python. To define a nullable field simply use an optional type:

.. code-block:: python

   @dataclass
   class Player(Model):
       """A player model."""

       nickname: TextField
       email: TextField | None

While ``nickname`` column has `NOT NULL` set by default, the ``email`` column has not.

All other column properties are configured through ``Annotated`` types:

.. code-block:: python

   @dataclass
   class Player(Model):
       """A player model."""

       nickname: Annotated[TextField, Fieldmeta(unique=True)]


Declaring relationships
-----------------------

All relationships are declared though the :py:class:`ForeignKeyField <sqls.models.ForeignKeyField>` type.

.. code-block:: python

   @dataclass
   class Player(Model):
       """A player model."""

       team_id: ForeignKeyField

From the field name ``team_id`` SQLs will derive that the player table will have a column called ``team_id`` that references the ``id`` field on the ``Team`` model. The reference can also be overridden manually:

.. code-block:: python

   @dataclass
   class Player(Model):
       """A player model."""

       team_id: Annotated[ForeignKeyField, Fieldmeta(foreign_key=('squad', 'id'))

SQL represents many-to-many relationships between two tables through a third `linking` table. From the point of view of the SQLs modeller a linking table is just like any other table:

.. code-block:: python

   @dataclass
   class PlayerTeam(Model):
       """Player team relationship."""

       id: None
       player_id: ForeignKeyField
       team_id: ForeignKeyField


Create database tables
----------------------

The :py:func:`get_create_queries <sqls.models.get_create_queries>` function takes a sequence of model classes and returns appropriate ``CREATE TABLE`` and ``CREATE INDEX`` queries:

.. code-block:: python

   from sqls.models import get_create_queries

   for query in get_create_queries([Player, PlayerTeam, Team]):
       await txn.exq(query)
