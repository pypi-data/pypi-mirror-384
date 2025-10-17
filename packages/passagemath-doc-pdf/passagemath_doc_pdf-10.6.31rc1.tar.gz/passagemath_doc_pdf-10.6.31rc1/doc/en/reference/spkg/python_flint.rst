.. _spkg_python_flint:

python_flint: Bindings for FLINT and Arb
========================================

Description
-----------

Bindings for FLINT and Arb

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/python-flint/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_flint`

Version Information
-------------------

package-version.txt::

    0.8.0

version_requirements.txt::

    python-flint

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install python-flint

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i python_flint


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
