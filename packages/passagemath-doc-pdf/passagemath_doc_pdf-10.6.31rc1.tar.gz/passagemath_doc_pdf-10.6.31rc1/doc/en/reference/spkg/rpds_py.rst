.. _spkg_rpds_py:

rpds_py: Python bindings to Rust's persistent data structures (rpds)
====================================================================

Description
-----------

Python bindings to Rust's persistent data structures (rpds)

In SageMath, this package is used as a dependency package of the
Jupyter notebook / JupyterLab.

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/rpds-py/



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

    0.25.0

version_requirements.txt::

    rpds-py

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install rpds-py

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i rpds_py


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
