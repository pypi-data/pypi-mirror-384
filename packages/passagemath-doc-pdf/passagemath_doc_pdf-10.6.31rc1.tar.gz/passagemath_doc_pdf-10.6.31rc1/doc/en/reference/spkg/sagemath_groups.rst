.. _spkg_sagemath_groups:

=============================================================================================
sagemath_groups: Groups and Invariant Theory
=============================================================================================


This pip-installable package ``passagemath-groups`` a distribution of a part of the Sage Library.  It provides a small subset of the modules of the Sage library ("sagelib", ``passagemath-standard``) for computations with groups.


What is included
----------------

* `Groups <https://passagemath.org/docs/latest/html/en/reference/groups/index.html>`_

* see https://github.com/passagemath/passagemath/blob/main/pkgs/sagemath-groups/MANIFEST.in


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_gmp`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_gap`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-groups == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-groups==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_groups


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
