.. _spkg_networkx:

networkx: Python package for complex networks
=============================================

Description
-----------

NetworkX (NX) is a Python package for the creation, manipulation, and
study of the structure, dynamics, and functions of complex networks.

License
-------

BSD


Upstream Contact
----------------

https://networkx.github.io/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_scipy`

Version Information
-------------------

package-version.txt::

    3.4.2

src/pyproject.toml::

    networkx >=2.4

version_requirements.txt::

    networkx

See https://repology.org/project/python:networkx/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install networkx\>=2.4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i networkx

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-networkx

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install networkx\<3.3\,\>=2.4

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-networkx

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-networkx

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/networkx

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-networkx

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-networkx

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-networkx


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
