.. _spkg_tornado:

tornado: Python web framework and asynchronous networking library
=================================================================

Description
-----------

Python web framework and asynchronous networking library

License
-------

Apache License


Upstream Contact
----------------

Home page: http://www.tornadoweb.org

Dependencies
------------

Python


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_certifi`

Version Information
-------------------

package-version.txt::

    6.4

version_requirements.txt::

    tornado >=6.0.4

See https://repology.org/project/python:tornado/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install tornado\>=6.0.4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i tornado

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install tornado

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-tornado

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge www-servers/tornado

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-tornado

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-tornado

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-tornado


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
