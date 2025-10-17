.. _spkg_arithmat:

arithmat: Sage implementation of arithmetic matroids and toric arrangements
===========================================================================

Description
-----------

Sage implementation of arithmetic matroids and toric arrangements

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/arithmat/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    arithmat @ git+https://github.com/passagemath/passagemath-pkg-arithmat

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install arithmat@git+https://github.com/passagemath/passagemath-pkg-arithmat

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i arithmat


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
