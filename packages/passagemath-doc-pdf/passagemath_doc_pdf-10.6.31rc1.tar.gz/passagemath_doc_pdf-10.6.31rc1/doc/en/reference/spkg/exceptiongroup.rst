.. _spkg_exceptiongroup:

exceptiongroup: Backport of PEP 654 (exception groups)
======================================================

Description
-----------

Backport of PEP 654 (exception groups)

License
-------

Upstream Contact
----------------

https://pypi.org/project/exceptiongroup/



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

    1.3.0

version_requirements.txt::

    exceptiongroup >=1.2.0

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install exceptiongroup\>=1.2.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i exceptiongroup


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
