.. _spkg_kerrgeodesic_gw:

kerrgeodesic_gw: Gravitational radiation from material orbiting a Kerr black hole
=================================================================================

Description
-----------

Gravitational radiation from material orbiting a Kerr black hole

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/kerrgeodesic-gw/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    kerrgeodesic-gw

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install kerrgeodesic-gw

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i kerrgeodesic_gw


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
