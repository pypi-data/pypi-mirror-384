.. _spkg_zftools:

zftools: Find the zero forcing set of graphs
============================================

Description
-----------

Find the zero forcing set of graphs

License
-------

GPLv3

Upstream Contact
----------------

- https://pypi.org/project/zftools/
- https://github.com/passagemath/passagemath-pkg-zftools


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    zftools @ git+https://github.com/passagemath/passagemath-pkg-zftools.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install zftools@git+https://github.com/passagemath/passagemath-pkg-zftools.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i zftools


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
