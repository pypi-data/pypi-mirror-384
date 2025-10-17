.. _spkg_jupyter_server_terminals:

jupyter_server_terminals: A Jupyter Server Extension Providing Terminals
========================================================================

Description
-----------

A Jupyter Server Extension Providing Terminals.

License
-------

Modified BSD License (also known as New or Revised or 3-Clause BSD)

Upstream Contact
----------------

https://pypi.org/project/jupyter-server-terminals/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_terminado`

Version Information
-------------------

package-version.txt::

    0.4.4

version_requirements.txt::

    jupyter-server-terminals

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-server-terminals

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_server_terminals


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
