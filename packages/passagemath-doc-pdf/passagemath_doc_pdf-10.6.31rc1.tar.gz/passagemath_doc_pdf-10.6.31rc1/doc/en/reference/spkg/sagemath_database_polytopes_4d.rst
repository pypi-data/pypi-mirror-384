.. _spkg_sagemath_database_polytopes_4d:

====================================================================================
sagemath_database_polytopes_4d: Database of 4-dimensional reflexive polytopes
====================================================================================


This pip-installable distribution ``passagemath-database-polytopes-4d`` is a
distribution of data for use with ``passagemath-polyhedra``.

It provides the database of 4-d reflexive polytopes with Hodge
numbers as index, based on the original list by Maximilian Kreuzer
and Harald Skarke using their software PALP.

Because the database is huge, there is no wheel provided on PyPI.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_polytopes_db_4d`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-database-polytopes-4d == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-database-polytopes-4d==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_database_polytopes_4d


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
