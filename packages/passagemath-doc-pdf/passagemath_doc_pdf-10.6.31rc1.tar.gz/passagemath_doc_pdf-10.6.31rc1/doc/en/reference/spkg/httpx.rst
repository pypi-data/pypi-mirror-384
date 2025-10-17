.. _spkg_httpx:

httpx: The next generation HTTP client.
=======================================

Description
-----------

The next generation HTTP client.

License
-------

Upstream Contact
----------------

https://pypi.org/project/httpx/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_anyio`
- :ref:`spkg_httpcore`
- :ref:`spkg_pip`
- :ref:`spkg_sniffio`

Version Information
-------------------

package-version.txt::

    0.28.1

version_requirements.txt::

    httpx

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install httpx

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i httpx


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
