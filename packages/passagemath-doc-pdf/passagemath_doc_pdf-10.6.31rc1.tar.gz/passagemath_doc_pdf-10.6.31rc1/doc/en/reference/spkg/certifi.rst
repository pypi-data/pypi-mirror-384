.. _spkg_certifi:

certifi: Python package for providing Mozilla's CA Bundle
=========================================================

Description
-----------

Python package for providing Mozilla's CA Bundle.

License
-------

MPL-2.0

Upstream Contact
----------------

https://pypi.org/project/certifi/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    2025.6.15

version_requirements.txt::

    certifi >=2020.6.20

See https://repology.org/project/python:certifi/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install certifi\>=2020.6.20

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i certifi

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-certifi

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install certifi

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-certifi

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-certifi

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/certifi

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-certifi

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-certifi

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-certifi


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
