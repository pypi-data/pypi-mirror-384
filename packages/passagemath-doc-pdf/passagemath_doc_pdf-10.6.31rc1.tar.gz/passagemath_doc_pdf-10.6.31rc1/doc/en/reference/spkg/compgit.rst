.. _spkg_compgit:

compgit: Computing Geometric Invariant Theory (GIT) quotients in algebraic geometry
===================================================================================

Description
-----------

The CompGIT package is a tool for computing Geometric Invariant Theory (GIT) quotients in algebraic geometry. In a nutshell, GIT is a theory to model orbit spaces of algebraic varieties. Given an action of a simple complex reductive group $G$ on a projective space $\mathbb{P}^n$, CompGIT gives a description of the $G$-orbits of $\mathbb{P}^n$, called unstable/non-stable/strictly polystable orbits, that need to be removed/treated specially to form a well-behaved quotient.

License
-------

GNU General Public License v3.0

Upstream Contact
----------------

- https://github.com/passagemath/passagemath-pkg-CompGIT
- https://github.com/Robbie-H/CompGIT


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_scipy`

Version Information
-------------------

requirements.txt::

    CompGIT @ git+https://github.com/passagemath/passagemath-pkg-CompGIT

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install CompGIT@git+https://github.com/passagemath/passagemath-pkg-CompGIT

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i compgit


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
