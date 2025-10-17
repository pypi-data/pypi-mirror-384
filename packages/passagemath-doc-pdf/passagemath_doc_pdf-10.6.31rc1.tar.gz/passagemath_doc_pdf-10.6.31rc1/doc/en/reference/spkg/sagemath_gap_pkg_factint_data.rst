.. _spkg_sagemath_gap_pkg_factint_data:

=====================================================================================================
sagemath_gap_pkg_factint_data: Computational Group Theory with GAP: factint data
=====================================================================================================


This pip-installable distribution ``passagemath-gap-pkg-factint-data`` is a
distribution of data for use with ``passagemath-gap``.


What is included
----------------

- Wheels on PyPI include the data files of the GAP factint package


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-gap-pkg-factint-data == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gap-pkg-factint-data==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gap_pkg_factint_data


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
