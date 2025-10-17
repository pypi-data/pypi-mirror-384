.. _spkg_database_knotinfo:

database_knotinfo: Content of the KnotInfo and LinkInfo databases as lists of dictionaries
==========================================================================================

Description
-----------

Content of the KnotInfo and LinkInfo databases as lists of dictionaries

License
-------

GPL

Upstream Contact
----------------

https://pypi.org/project/database-knotinfo/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    2024.10.1

version_requirements.txt::

    database-knotinfo

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install database-knotinfo

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i database_knotinfo


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
