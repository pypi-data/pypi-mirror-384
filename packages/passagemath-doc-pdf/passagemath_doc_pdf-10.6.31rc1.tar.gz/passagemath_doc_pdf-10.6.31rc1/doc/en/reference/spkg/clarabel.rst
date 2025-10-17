.. _spkg_clarabel:

clarabel: Clarabel Conic Interior Point Solver for Rust / Python
================================================================

Description
-----------

Clarabel Conic Interior Point Solver for Rust / Python

License
-------

Apache-2.0

Upstream Contact
----------------

https://pypi.org/project/clarabel/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_numpy`
- :ref:`spkg_pip`
- :ref:`spkg_scipy`

Version Information
-------------------

package-version.txt::

    0.9.0

version_requirements.txt::

    clarabel

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install clarabel

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i clarabel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
