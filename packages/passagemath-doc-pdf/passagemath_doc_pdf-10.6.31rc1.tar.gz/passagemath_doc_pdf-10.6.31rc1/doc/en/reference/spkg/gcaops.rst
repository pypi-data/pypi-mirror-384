.. _spkg_gcaops:

gcaops: Graph complex action on Poisson structures
==================================================

Description
-----------

A python package implementing the action of Kontsevich's graph complex(es)
on Poisson structures.

License
-------

MIT

Upstream Contact
----------------

- https://github.com/rburing/gcaops
- https://github.com/passagemath/passagemath-pkg-gcaops


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_nauty`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    gcaops @ git+https://github.com/passagemath/passagemath-pkg-gcaops.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install gcaops@git+https://github.com/passagemath/passagemath-pkg-gcaops.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gcaops


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
