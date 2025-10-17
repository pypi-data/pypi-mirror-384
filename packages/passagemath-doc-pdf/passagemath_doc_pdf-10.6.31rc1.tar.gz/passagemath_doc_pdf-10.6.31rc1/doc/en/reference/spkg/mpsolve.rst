.. _spkg_mpsolve:

mpsolve: Multiprecision polynomial solver
=========================================

Description
-----------

MPSolve stands for Multiprecision Polynomial SOLVEr. It is a software that aims to provide an easy to use (hopefully) universal blackbox for solving polynomials and secular equations.


License
-------

GPL v3+


Upstream Contact
----------------

https://numpi.dm.unipi.it/scientific-computing-libraries/mpsolve/

https://github.com/robol/MPSolve


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg__bootstrap`

Version Information
-------------------

package-version.txt::

    3.2.1

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i mpsolve


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
