.. _spkg_recip:

recip: Package for Igusa class polynomials, CM fields, and Shimura's reciprocity law
====================================================================================

Description
-----------

Package for Igusa class polynomials, CM fields, and Shimura's reciprocity law

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/recip/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_schemes`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    recip @ git+https://github.com/passagemath/passagemath-pkg-recip.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install recip@git+https://github.com/passagemath/passagemath-pkg-recip.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i recip


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
