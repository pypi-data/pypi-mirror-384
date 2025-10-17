.. _spkg_notebook_shim:

notebook_shim: A shim layer for notebook traits and config
==========================================================

Description
-----------

A shim layer for notebook traits and config

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/notebook-shim/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_jupyter_server`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    0.2.3

version_requirements.txt::

    notebook-shim

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install notebook-shim

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i notebook_shim


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
