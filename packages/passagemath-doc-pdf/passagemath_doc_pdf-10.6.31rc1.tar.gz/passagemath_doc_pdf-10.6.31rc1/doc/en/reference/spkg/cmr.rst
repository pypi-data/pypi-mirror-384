.. _spkg_cmr:

cmr: Combinatorial matrix recognition
=====================================

Description
-----------

The following matrix classes can be recognized:

- Totally Unimodular Matrices
- Network Matrices
- Complement Totally Unimodular Matrices
- (Strongly) k-Modular and Unimodular Matrices

Moreover, representation matrices for the following matroid classes can be recognized:

- Regular Matroids
- Graphic / Cographic / Planar Matrices
- Series-Parallel Matroids


License
-------

MIT license


Upstream Contact
----------------

https://discopt.github.io/cmr/

https://github.com/discopt/cmr


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_cmake`
- :ref:`spkg_googletest`
- :ref:`spkg_ninja_build`

Version Information
-------------------

package-version.txt::

    1.4

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cmr


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
