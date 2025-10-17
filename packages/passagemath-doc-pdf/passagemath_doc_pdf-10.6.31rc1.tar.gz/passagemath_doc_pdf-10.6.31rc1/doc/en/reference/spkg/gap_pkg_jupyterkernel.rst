.. _spkg_gap_pkg_jupyterkernel:

gap_pkg_jupyterkernel: Native Jupyter kernel for GAP
====================================================

Description
-----------

This GAP package implements the Jupyter protocol.

It is shipped together with some GAP packages that are dependencies
or additional functionality.

See also: ``sagemath_gap_pkg_jupyterkernel``


License
-------

BSD-3-Clause license


Upstream Contact
----------------

- https://github.com/gap-packages/JupyterKernel
- https://github.com/nathancarter/jupyterviz


Type
----

optional


Dependencies
------------

- :ref:`spkg_gap`
- :ref:`spkg_gap_packages`
- :ref:`spkg_zeromq`

Version Information
-------------------

package-version.txt::

    4.15.0

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gap_pkg_jupyterkernel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
