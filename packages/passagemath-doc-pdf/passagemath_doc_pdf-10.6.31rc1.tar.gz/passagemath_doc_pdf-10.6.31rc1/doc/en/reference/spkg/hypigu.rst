.. _spkg_hypigu:

hypigu: Compute the Igusa local zeta function associated with hyperplane arrangements
=====================================================================================

Description
-----------

SageMath package that provides functions to compute the Igusa local zeta function associated with hyperplane arrangements

License
-------

MIT

Upstream Contact
----------------

- https://pypi.org/project/hypigu/
- https://github.com/passagemath/passagemath-pkg-hypigu


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_gap`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    hypigu @ git+https://github.com/passagemath/passagemath-pkg-hypigu.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install hypigu@git+https://github.com/passagemath/passagemath-pkg-hypigu.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i hypigu


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
