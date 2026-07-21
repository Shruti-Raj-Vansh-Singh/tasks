python-sqlparse - Parse SQL statements
======================================

|buildstatus|_
|coverage|_
|docs|_
|packageversion|_

.. docincludebegin

sqlparse is a non-validating SQL parser for Python.
It provides support for parsing, splitting and formatting SQL statements.

The module is compatible with Python 3.8+ and released under the terms of the
`New BSD license <https://opensource.org/licenses/BSD-3-Clause>`_.

Visit the project page at https://github.com/andialbrecht/sqlparse for
further information about this project.


Quick Start
-----------

.. code-block:: sh

   $ pip install sqlparse

.. code-block:: python

   >>> import sqlparse

   >>> # Split a string containing two SQL statements:
   >>> raw = 'select * from foo; select * from bar;'
   >>> statements = sqlparse.split(raw)
   >>> statements
   ['select * from foo;', 'select * from bar;']

   >>> # Format the first statement and print it out:
   >>> first = statements[0]
   >>> print(sqlparse.format(first, reindent=True, keyword_case='upper'))
   SELECT *
   FROM foo;

   >>> # Parsing a SQL statement:
   >>> parsed = sqlparse.parse('select * from foo')[0]
   >>> parsed.tokens
   [<DML 'select' at 0x7f22c5e15368>, <Whitespace ' ' at 0x7f22c5e153b0>, <Wildcard '*' … ]
   >>>

Pre-commit Hook
---------------

sqlparse can be used as a `pre-commit <https://pre-commit.com/>`_ hook
to automatically format SQL files before committing:

.. code-block:: yaml

   repos:
     - repo: https://github.com/andialbrecht/sqlparse
       rev: 0.5.4  # Use the latest version
       hooks:
         - id: sqlformat
           # Optional: Add more formatting options
           # IMPORTANT: --in-place is required, already included by default
           args: [--in-place, --reindent, --keywords, upper]

Then install the hook:

.. code-block:: sh

   $ pre-commit install

Your SQL files will now be automatically formatted on each commit.

**Note**: The hook uses ``--in-place --reindent`` by default. If you override
the ``args``, you **must** include ``--in-place`` for the hook to work.

Links
-----

Project page
   https://github.com/andialbrecht/sqlparse

Bug tracker
   https://github.com/andialbrecht/sqlparse/issues

Documentation
   https://sqlparse.readthedocs.io/

Online Demo
   https://sqlformat.org/


sqlparse is licensed under the BSD license.

Parts of the code are based on pygments written by Georg Brandl and others.
pygments-Homepage: http://pygments.org/

.. |buildstatus| image:: https://github.com/andialbrecht/sqlparse/actions/workflows/python-app.yml/badge.svg
.. _buildstatus: https://github.com/andialbrecht/sqlparse/actions/workflows/python-app.yml
.. |coverage| image:: https://codecov.io/gh/andialbrecht/sqlparse/branch/master/graph/badge.svg
.. _coverage: https://codecov.io/gh/andialbrecht/sqlparse
.. |docs| image:: https://readthedocs.org/projects/sqlparse/badge/?version=latest
.. _docs: https://sqlparse.readthedocs.io/en/latest/?badge=latest
.. |packageversion| image:: https://img.shields.io/pypi/v/sqlparse?color=%2334D058&label=pypi%20package
.. _packageversion: https://pypi.org/project/sqlparse
