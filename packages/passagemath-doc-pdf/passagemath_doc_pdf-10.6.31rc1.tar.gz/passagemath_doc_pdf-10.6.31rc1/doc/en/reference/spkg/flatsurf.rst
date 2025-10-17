.. _spkg_flatsurf:

flatsurf: Flat surfaces in SageMath
===================================

Description
-----------

SageMath package for studying the geometry of flat surfaces and the
dynamics of their foliations.

License
-------

GNU General Public License, version 2

Upstream Contact
----------------

https://pypi.org/project/sage-flatsurf/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- $(SAGERUNTIME)
- :ref:`spkg_surface_dynamics`

Version Information
-------------------

requirements.txt::

    sage-flatsurf

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sage-flatsurf

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i flatsurf


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
