.. _spkg_tzlocal:

tzlocal: Python timezone information for the local timezone
===========================================================

Description
-----------

tzinfo object for the local timezone


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pytz_deprecation_shim`

Version Information
-------------------

package-version.txt::

    5.0.1

version_requirements.txt::

    tzlocal >=2.1

See https://repology.org/project/tzlocal/versions, https://repology.org/project/python:tzlocal/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install tzlocal\>=2.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i tzlocal

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-tzlocal

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install tzlocal

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-tzlocal

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-tzlocal

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-tzlocal

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/tzlocal

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-tzlocal

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-tzlocal

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-tzlocal


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
