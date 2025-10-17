.. _spkg_fricas:

fricas: A general purpose computer algebra system
=================================================

Description
-----------

FriCAS is a general purpose computer algebra system.

License
-------

Modified BSD license.


Upstream Contact
----------------

https://github.com/fricas/fricas


Type
----

optional


Dependencies
------------

- :ref:`spkg_ecl`

Version Information
-------------------

package-version.txt::

    1.3.12

See https://repology.org/project/fricas/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i fricas

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install fricas

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/fricas

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/fricas

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install fricas

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install fricas

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install fricas


If the system package is installed, ``./configure`` will check if it can be used.
