.. _spkg_euler_product:

euler_product: Number theory with Euler products
================================================

Description
-----------

This Sage packages enables investigations in number theory using Euler products.

License
-------

GPLv3.0

Upstream Contact
----------------

- https://pypi.org/project/sage-euler-product/
- https://github.com/passagemath/passagemath-pkg-euler-product


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_schemes`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    sage-euler-product @ git+https://github.com/passagemath/passagemath-pkg-euler-product.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sage-euler-product@git+https://github.com/passagemath/passagemath-pkg-euler-product.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i euler_product


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
