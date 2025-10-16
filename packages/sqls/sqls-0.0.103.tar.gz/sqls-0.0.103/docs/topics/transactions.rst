Transactions
============

In :py:mod:`sqls.transactions` SQLs provides asynchronous transaction managers.


Database backends
-----------------

Currently the following SQL databases are supported:

- MySQL/MariaDB (aiomysql)
- PostgreSQL (asyncpg)
- SQLite (aiosqlite)


Connecting to databases
-----------------------

The :py:func:`get_manager <sqls.transactions.get_manager>` function takes a database URI and returns a transaction manager instance:

.. code-block:: python

   from sqls.transactions import get_manager

   manager = get_manager('<URI>')
   await manager.init()

   # Use manager in your program.

   await manager.close()

The function takes an URI and returns an appropriate manager instance. Managers need to be initialized before use and should be closed when not needed anymore.

SQLite
^^^^^^

The ``file:`` scheme is used to refer to SQLite databases:

.. code-block:: python

   manager = get_manager('file:///path/to/sqlite.db')

MySQL
^^^^^

Use URIs with the ``mysql:`` scheme to connect to MySQL databases:

.. code-block:: python

   manager = get_manager('mysql://user:pass@server:port/databasename')

PostgreSQL
^^^^^^^^^^

Use URIs with the ``postgresql:`` scheme to connect to PostgreSQL databases:

.. code-block:: python

   manager = get_manager('postgresql://user:pass@server:port/databasename')


Handling transactions
---------------------

Managers can create transactions objects with :py:meth:`txn <sqls.interfaces.Manager.txn>`. Those objects can be used as asynchronous context managers to automatically open/commit/rollback database transactions.

.. code-block:: python

   async with manager.txn() as txn:
       await txn.execute('SELECT 1')

On entering the context manager a new database transaction is created. If the code in the context throws an exception the transaction will be rolled back and otherwise committed automatically.

Multiple open transactions are allowed to exist at the same time. The necessary support for concurrency is already provided by the underlying database implementations.


Running queries
---------------

Open transactions can execute manually written queries:

.. code-block:: python

   async with manager.txn() as txn:
       # Run simple string.
       await txn.execute('SELECT 1')

       # Use placeholders to avoid injection attacks.
       await txn.execute('SELECT id FROM user WHERE name=?', 'Ringo')


Open transactions can also execute constructed query objects:

.. code-block:: python

   query = Query().select(ExprLiteral(1).typed(int))

   async with manager.txn() as txn:
       # Execute constructed query.
       await txn.exq(query)

While constructed queries are arguably more convenient to write, they have the added benefit, that the return value of ``.exq`` will be fully typed and static type checkers will know the type of each returned column.
