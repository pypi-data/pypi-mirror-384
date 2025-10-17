.. _spkg_sagemath_gap_pkg_cddinterface:

=================================================================================================
sagemath_gap_pkg_cddinterface: Computational Group Theory with GAP: cddinterface package
=================================================================================================


This pip-installable distribution ``passagemath-gap-pkg-cddinterface`` is a
distribution of the GAP package ``cddinterface`` for use with ``passagemath-gap``.


What is included
----------------

- Wheels on PyPI include the GAP package ``cddinterface``


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_gap_packages`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-gap-pkg-cddinterface == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gap-pkg-cddinterface==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gap_pkg_cddinterface


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
