.. _spkg_pplpy_doc:

pplpy_doc: Python interface to the Parma Polyhedra Library (documentation)
==========================================================================

Description
-----------

PPL Python wrapper (documentation)

The Python package pplpy provides a wrapper to the C++ Parma Polyhedra
Library (PPL).

The whole package started as a fork of a tiny part of the Sage library.

We are using the compatible fork passagemath-ppl.

License
-------

GPL version 3


Upstream Contact
----------------

-  https://github.com/passagemath/passagemath-ppl


Type
----

standard


Dependencies
------------

- :ref:`spkg_pplpy`
- :ref:`spkg_sphinx`

Version Information
-------------------

package-version.txt::

    0.8.10.1

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pplpy_doc


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
