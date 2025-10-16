Queries
=======

The :py:mod:`sqls.queries` packages provides tools to formulate SQL queries in idiomatic, fully-typed Python. This package is currently tailored around the SQLite dialect, but can also be used for MySQL and PostgreSQL.


Tables
------

Tables are referred to from Python though instances of the :py:class:`Table <sqls.queries.Table>` class:

.. code-block:: python

   from sqls.queries import Table

   player = Table('player')

To refer to columns of a table simply use the attribute syntax:

.. code-block:: python

   player = Table('player')
   name = player.name

In queries the ``name`` variable will expand to ``"player"."name"``.

Dynamic and star access
^^^^^^^^^^^^^^^^^^^^^^^

To reference all columns or use dynamic column names you can use the ``/``-Syntax:

.. code-block:: python

   player = Table('player')

   # Dynamic column reference.
   colname = 'nickname'

   star = player / '*'
   dynamic = player / colname

In queries ``star`` will expand to ``"player".*`` and ``dynamic`` will expand to ``"player"."nickname"``.

Table alias
^^^^^^^^^^^

Tables can be aliased to a new name:

.. code-block:: python

   player = Table('player')
   user = player.as_('user')
   name = user.name

In queries the ``name`` variable will expand to ``"user"."name"``.


Joins
-----

Joins are build though the :py:class:`Join <sqls.queries.Join>` builder class:

.. code-block:: python

   from sqls.queries import Join, Table

   player = Table('player')
   team = Table('team')

   # Outer () allow line breaks for readability.
   join = (
       # Create empty join.
       Join()
       # Add first table.
       .join(player)
       # Add second table.
       .join(team)
       # Constrain join.
       .on_(player.team_id == team.id)
   )

The chain of ``.join`` and ``.on_`` can be extended as needed to join more than two tables. Any ``.join`` call after the first takes an optional second argument ``typ`` that can be used to set the join type:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   # If players might not be assigned to a team, a left join is more appropriate.
   join = (
       Join()
       .join(player)
       .join(team, typ='left')
       .on_(player.team_id == team.id)
   )

Most SQLs interfaces take Table and Join arguments interchangeably in a similar way SQL itself does.


Expressions
-----------

Expressions play an important role in the SQL syntax. For example, referencing a column or using a literal can already be interpreted an expression. In SQLs expressions are represented through objects of the :py:class:`Expr <sqls.queries.expr.Expr>` class. When using ``sqls.queries`` you will create expressions mostly in one of the following ways:

.. code-block:: python

   from sqls.queries import ExprLiteral, Table

   player = Table('player')

   # Referencing the column of a table yields a column expression.
   highscore = player.highscore

   # Any kind of operation on an existing expression creates a new expression.
   is_better = highscore > 100

   # Converting a Python literal manually to a SQLs literal.
   onehundred = ExprLiteral(100)

The explicit creation of expressions with ``ExprLiteral`` is mostly needed for expressions where the most left hand operand is a literal value.

Function invocation
^^^^^^^^^^^^^^^^^^^

Function invocations are also expressions:

.. code-block:: python

   from sqls.queries import ExprFunction

   scoresum = ExprFunction('SUM', player.highscore)

Type annotations
^^^^^^^^^^^^^^^^

When writing queries you know usually know what Python type an expression will yield. To this end SQLs expressions can be type annotated:

.. code-block:: python

   player = Table('player')

   # Make Python understand this expression yields and int
   highscore = player.highscore.typed(int)


Building queries
----------------

All queries start with instances of the :py:class:`Query <sqls.queries.Query>` class. A code editor with Python language server support should give very good completion options on query builder objects.

.. code-block:: python

   from sqls.queries import Query

   query = Query()

Insert
^^^^^^

Insert queries are initiated with any of:

- :py:meth:`insert <sqls.queries.Query.insert>`
- :py:meth:`insert_or_abort <sqls.queries.Query.insert_or_abort>`
- :py:meth:`insert_or_fail <sqls.queries.Query.insert_or_fail>`
- :py:meth:`insert_or_ignore <sqls.queries.Query.insert_or_ignore>`
- :py:meth:`insert_or_replace <sqls.queries.Query.insert_or_replace>`
- :py:meth:`insert_or_rollback <sqls.queries.Query.insert_or_rollback>`

.. code-block:: python

   player = Table('player')

   # Outer () allows line breaks for readability.
   query = (
       Query()
       .insert(player)
       .columns(player.name, player.highscore)
       .values(
           ('Ringo', 100),
           ('John', 97),
       )
   )

   # Insert values from other query.
   query = (
       Query()
       .insert(player)
       .columns(player.name, player.highscore)
       .select(some_select_query)
   )

   # Resolve insert conflicts with ON CONFLICT.
   excluded = Table('excluded')
   query = (
       Query()
       .insert(player)
       .columns(player.name, player.highscore)
       .values(
           ('Ringo', 100),
           ('John', 97),
       )
       .on_conflict(player.name)
       .update_set((player.highscore,), (excluded.highscore,))
       .where(excluded.highscore > player.highscore)
   )

Update
^^^^^^

Update queries are initiated with any of:

- :py:meth:`update <sqls.queries.Query.update>`
- :py:meth:`update_or_abort <sqls.queries.Query.update_or_abort>`
- :py:meth:`update_or_fail <sqls.queries.Query.update_or_fail>`
- :py:meth:`update_or_ignore <sqls.queries.Query.update_or_ignore>`
- :py:meth:`update_or_replace <sqls.queries.Query.update_or_replace>`
- :py:meth:`update_or_rollback <sqls.queries.Query.update_or_rollback>`

.. code-block:: python

   player = Table('player')

   # Update all rows.
   query = (
       Query()
       .update(player)
       .set(
           (player.highscore,),
           (0,),
       )
   )

   # Update single row.
   query = (
       Query()
       .update(player)
       .set(
           (player.highscore,),
           (100,),
       )
       .where(player.name == 'Ringo')
   )

   # Update with data from other table or query.
   other = Table('newscores')
   query = (
       Query()
       .update(player)
       .set(
           (player.highscore,),
           (other.highscore,),
       )
       .from_(other)
       .where(player.name == other.name)
   )


Delete
^^^^^^

Delete queries are initiated with :py:meth:`delete <sqls.queries.Query.delete>`:

.. code-block:: python

   player = Table('player')

   # Delete low performing players.
   query = (
       Query()
       .delete(player)
       .where(player.highscore < 20)
   )

Select
^^^^^^

Select queries are initiated with :py:meth:`select <sqls.queries.Query.select>` :

.. code-block:: python

   player = Table('player')

   query = (
       Query()
       .select(
           player.name.typed(str),
           player.highscore.typed(int),
        )
        .from_(player)
   )

From join
"""""""""

The ``from_`` method accepts also joins:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   query = (
       Query()
       .select(
           player.name.typed(str),
           player.highscore.typed(int),
           team.name.typed(str),
        )
        .from_(
            Join()
            .join(player)
            .join(team).on_(player.team_id == team.id),
        ),
   )

Filter with where
"""""""""""""""""

The ``where`` method accepts any expression:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   query = (
       Query()
       .select(
           player.name.typed(str),
           player.highscore.typed(int),
           team.name.typed(str),
       )
       .from_(
           Join()
           .join(player)
           .join(team).on_(player.team_id == team.id),
       ),
       .where(player.highscore > 90)
   )

Group rows
""""""""""

The ``group_by`` method accepts any expression:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   # Query team names and their cumulative score.
   query = (
       Query()
       .select(
           team.name.typed(str),
           ExprFunction('SUM', player.highscore).as_('score').typed(int),
       )
       .from_(
           Join()
           .join(player)
           .join(team).on_(player.team_id == team.id),
       )
       .group_by(team.id)
   )

   # Filter for teams with score higher than 200.
   query = (
       query
       .having(ExprFunction('SUM', player.highscore) > 200)
   )

Sorting
"""""""

The ``order_by`` method accepts multiple expressions to sort by:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   # Query team names and player names in alphabetical order.
   query = (
       Query()
       .select(
           team.name.typed(str),
           player.name.typed(str),
       )
       .from_(
           Join()
           .join(player)
           .join(team).on_(player.team_id == team.id),
       )
       .order_by(team.name, player.name)
   )

Additionally, ``order_by`` accepts a keyword argument ``desc`` to switch to descending sort order.

Limit
"""""

The ``limit`` method narrows the number of returned rows:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   # Limit number of returned rows to 10.
   query = (
       Query()
       .select(
           team.name.typed(str),
           ExprFunction('SUM', player.highscore).as_('score').typed(int),
       )
       .from_(
           Join()
           .join(player)
           .join(team).on_(player.team_id == team.id),
       )
       .limit(10)
   )

Offset
""""""

The ``offset`` method selects the starting row of the limited return set:

.. code-block:: python

   player = Table('player')
   team = Table('team')

   # Select the next 10 rows.
   query = (
       Query()
       .select(
           team.name.typed(str),
           ExprFunction('SUM', player.highscore).as_('score').typed(int),
       )
       .from_(
           Join()
           .join(player)
           .join(team).on_(player.team_id == team.id),
       )
       .limit(10)
       .offset(10)
   )

