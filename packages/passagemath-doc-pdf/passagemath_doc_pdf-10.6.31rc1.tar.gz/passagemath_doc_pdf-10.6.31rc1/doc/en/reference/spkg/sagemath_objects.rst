.. _spkg_sagemath_objects:

====================================================================================================================================
sagemath_objects: Sage objects, elements, parents, categories, coercion, metaclasses
====================================================================================================================================


The pip-installable distribution package ``passagemath-objects`` is a
distribution of a small part of the Sage Library.

It provides a small, fundamental subset of the modules of the Sage library
("sagelib", ``passagemath-standard``), making Sage objects, the element/parent
framework, categories, the coercion system and the related metaclasses
available.


Dependencies
------------

When building from source, development packages of ``gmp``, ``mpfr``, and ``mpc`` are needed.


Documentation
-------------

* `Categories <https://passagemath.org/docs/latest/html/en/reference/categories/index.html>`_

* `Structure <https://passagemath.org/docs/latest/html/en/reference/structure/index.html>`_

* `Coercion <https://passagemath.org/docs/latest/html/en/reference/coercion/index.html>`_

* `Classes, Metaclasses <https://passagemath.org/docs/latest/html/en/reference/misc/index.html#special-base-classes-decorators-etc>`_


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gmp`
- :ref:`spkg_gmpy2`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`
- :ref:`spkg_typing_extensions`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-objects == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-objects==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_objects


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
