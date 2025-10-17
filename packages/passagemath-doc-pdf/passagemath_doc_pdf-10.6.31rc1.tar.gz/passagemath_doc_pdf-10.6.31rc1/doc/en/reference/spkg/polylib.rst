.. _spkg_polylib:

polylib: Operations on unions of polyhedra
==========================================

Description
-----------

The Polyhedral Library (PolyLib for short) operates on objects made up
of unions of polyhedra of any dimension. polylib is a C library.

License
-------

GPL v3


Upstream Contact
----------------

-  https://groups.google.com/forum/#!forum/isl-development



Type
----

experimental


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_mpfr`
- :ref:`spkg_ntl`

Version Information
-------------------

package-version.txt::

    5.22.5

See https://repology.org/project/polylib/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i polylib

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install polylib

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install polylib pkgconfig\(polylibgmp\)


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
