.. _spkg_sagemath_database_cremona_ellcurve:

==================================================================
sagemath_database_cremona_ellcurve: Database of elliptic curves
==================================================================


This pip-installable distribution ``passagemath-database-cremona-ellcurve`` is a
distribution of data for use with ``passagemath-schemes``.

It provides John Cremona's `database of elliptic curves <https://github.com/JohnCremona/ecdata>`__.

Because the database is huge, there is no wheel provided on PyPI.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_database_cremona_ellcurve`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-database-cremona-ellcurve == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-database-cremona-ellcurve==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_database_cremona_ellcurve


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
