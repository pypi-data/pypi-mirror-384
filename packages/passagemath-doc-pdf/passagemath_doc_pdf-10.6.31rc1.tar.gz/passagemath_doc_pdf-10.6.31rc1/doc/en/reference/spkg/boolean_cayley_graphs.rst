.. _spkg_boolean_cayley_graphs:

boolean_cayley_graphs: Investigations of Boolean functions, their Cayley graphs, and associated structures
==========================================================================================================

Description
-----------

Investigations of Boolean functions, their Cayley graphs, and associated structures

License
-------

GPLv3

Upstream Contact
----------------

- https://pypi.org/project/boolean-cayley-graphs/
- https://github.com/passagemath/passagemath-pkg-Boolean-Cayley-graphs


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_brial`
- :ref:`spkg_sagemath_cliquer`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_gap`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    boolean-cayley-graphs @ git+https://github.com/passagemath/passagemath-pkg-Boolean-Cayley-graphs.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install boolean-cayley-graphs@git+https://github.com/passagemath/passagemath-pkg-Boolean-Cayley-graphs.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i boolean_cayley_graphs


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
