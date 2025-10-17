.. _spkg_libxml2:

libxml2: XML parser and toolkit
===============================

Description
-----------

XML C parser and toolkit

License
-------

MIT

Upstream Contact
----------------

http://www.xmlsoft.org/index.html


Type
----

optional


Dependencies
------------

- :ref:`spkg_iconv`
- :ref:`spkg_zlib`

Version Information
-------------------

See https://repology.org/project/libxml2/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add libxml2-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S libxml2

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libxml2-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libxml2-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install libxml2

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-libs/libxml2

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install libxml2

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-libxml2

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -libxml2

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr libxml2

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install libxml2

.. tab:: pyodide:

   install the following packages: libxml

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install libxml2

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install libxml2-devel


If the system package is installed, ``./configure`` will check if it can be used.
