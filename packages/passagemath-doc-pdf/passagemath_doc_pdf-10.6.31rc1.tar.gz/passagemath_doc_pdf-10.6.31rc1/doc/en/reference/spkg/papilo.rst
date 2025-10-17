.. _spkg_papilo:

papilo: Parallel presolve for integer and linear optimization
=============================================================

Description
-----------

parallel presolve routines for (mixed integer) linear programming
problems. The routines are implemented using templates which allows
switching to higher precision or rational arithmetic using the boost
multiprecision package.


License
-------

LGPL 3.0


Upstream Contact
----------------

https://github.com/scipopt/papilo/


Type
----

optional


Dependencies
------------

- $(BLAS)
- $(MP_LIBRARY)
- :ref:`spkg_boost_cropped`
- :ref:`spkg_cmake`
- :ref:`spkg_gfortran`
- :ref:`spkg_ninja_build`
- :ref:`spkg_onetbb`

Version Information
-------------------

package-version.txt::

    2.4.3

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i papilo


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
