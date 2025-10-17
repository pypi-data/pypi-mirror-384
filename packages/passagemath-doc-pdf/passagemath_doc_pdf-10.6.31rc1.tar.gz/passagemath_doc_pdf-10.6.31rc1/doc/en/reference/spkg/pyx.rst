.. _spkg_pyx:

pyx: Generate PostScript, PDF, and SVG files in Python
======================================================

Description
-----------

Python package for the generation of PostScript, PDF, and SVG files

https://pypi.python.org/pypi/PyX


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

requirements.txt::

    pyx

See https://repology.org/project/python:pyx/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pyx

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyx

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pyx

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-PyX

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pyx


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
