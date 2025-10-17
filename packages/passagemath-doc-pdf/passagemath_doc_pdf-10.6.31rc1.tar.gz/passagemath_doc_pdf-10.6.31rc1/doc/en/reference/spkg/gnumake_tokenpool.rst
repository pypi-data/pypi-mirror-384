.. _spkg_gnumake_tokenpool:

gnumake_tokenpool: Jobclient and jobserver for the GNU make tokenpool protocol
==============================================================================

Description
-----------

The project has implementations in multiple languages.

We only install the implementation in Python.


License
-------

MIT


Upstream Contact
----------------

- https://github.com/milahu/gnumake-tokenpool (upstream)


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

    0.0.7

version_requirements.txt::

    gnumake-tokenpool >= 0.0.4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install gnumake-tokenpool\>=0.0.4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gnumake_tokenpool


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
