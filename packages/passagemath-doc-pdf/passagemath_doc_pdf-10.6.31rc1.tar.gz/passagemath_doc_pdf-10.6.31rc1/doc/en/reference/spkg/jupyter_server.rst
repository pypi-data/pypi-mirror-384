.. _spkg_jupyter_server:

jupyter_server: The backend (core services, APIs, REST endpoints) to Jupyter web applications
=============================================================================================

Description
-----------

The backend, i.e., core services, APIs, and REST endpoints, to Jupyter web applications.

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/jupyter-server/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_anyio`
- :ref:`spkg_argon2_cffi`
- :ref:`spkg_jinja2`
- :ref:`spkg_jupyter_client`
- :ref:`spkg_jupyter_core`
- :ref:`spkg_jupyter_events`
- :ref:`spkg_jupyter_server_terminals`
- :ref:`spkg_nbconvert`
- :ref:`spkg_nbformat`
- :ref:`spkg_overrides`
- :ref:`spkg_pip`
- :ref:`spkg_platformdirs`
- :ref:`spkg_prometheus_client`
- :ref:`spkg_pyzmq`
- :ref:`spkg_send2trash`
- :ref:`spkg_terminado`
- :ref:`spkg_tornado`
- :ref:`spkg_traitlets`
- :ref:`spkg_websocket_client`

Version Information
-------------------

package-version.txt::

    2.7.3

version_requirements.txt::

    jupyter-server

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-server

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_server


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
