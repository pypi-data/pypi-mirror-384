.. _spkg_eigen:

eigen: C++ template library for linear algebra
==============================================

Description
-----------

Eigen is a C++ template library for linear algebra: matrices, vectors, numerical
solvers, and related algorithms.


License
-------

MPL 2


Upstream Contact
----------------

https://eigen.tuxfamily.org/index.php?title=Main_Page#Requirements


Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    3.4.0

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i eigen


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
