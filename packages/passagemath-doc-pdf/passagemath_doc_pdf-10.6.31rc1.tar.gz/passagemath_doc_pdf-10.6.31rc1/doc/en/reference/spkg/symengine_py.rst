.. _spkg_symengine_py:

symengine_py: Python wrappers for SymEngine
===========================================

Description
-----------

Python wrappers for SymEngine

License
-------

symengine.py is MIT licensed and uses several LGPL, BSD-3 and MIT
licensed libraries

Upstream Contact
----------------

https://github.com/symengine/symengine.py


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cmake`
- :ref:`spkg_cython`
- :ref:`spkg_symengine`

Version Information
-------------------

package-version.txt::

    0.11.0

version_requirements.txt::

    symengine.py >= 0.6.1

See https://repology.org/project/python:symengine/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install symengine.py\>=0.6.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i symengine_py

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-symengine

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install python-symengine

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/py-symengine

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/symengine


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
