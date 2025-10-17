.. _spkg_iconv:

iconv: Library for language/country-dependent character encodings
=================================================================

Description
-----------

GNU libiconv is a library that is used to enable different languages,
with different characters to be handled properly.

License
-------

-  GPL 3 and LGPL 3. So we can safely link against the library in Sage.


Upstream Contact
----------------

-  http://www.gnu.org/software/libiconv/
-  Bug reports to bug-gnu-libiconv@gnu.org


Type
----

standard


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/libiconv/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install libiconv

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install libiconv

.. tab:: pyodide:

   install the following packages: libiconv


If the system package is installed, ``./configure`` will check if it can be used.
