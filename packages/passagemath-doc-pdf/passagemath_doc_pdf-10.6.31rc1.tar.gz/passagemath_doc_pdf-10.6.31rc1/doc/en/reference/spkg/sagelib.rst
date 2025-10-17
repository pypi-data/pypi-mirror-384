.. _spkg_sagelib:

=========================================================================================
sagelib: Standard Python Library
=========================================================================================


This pip-installable distribution ``passagemath-standard`` is a metapackage
that provides all standard components of the Sage library.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_standard_no_symbolics`
- :ref:`spkg_sagemath_symbolics`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-standard == 10.6.31rc1

See https://repology.org/project/python:sagelib/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-standard==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagelib


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
