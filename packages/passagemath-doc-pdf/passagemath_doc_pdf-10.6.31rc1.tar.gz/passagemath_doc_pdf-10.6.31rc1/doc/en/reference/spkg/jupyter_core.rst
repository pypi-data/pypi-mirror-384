.. _spkg_jupyter_core:

jupyter_core: Jupyter core package
==================================

Description
-----------

Jupyter core package. A base package on which Jupyter projects rely.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_hatchling`
- :ref:`spkg_platformdirs`
- :ref:`spkg_traitlets`

Version Information
-------------------

package-version.txt::

    5.7.2

version_requirements.txt::

    jupyter-core

See https://repology.org/project/jupyter-core/versions, https://repology.org/project/python:jupyter-core/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-core

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_core

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jupyter_core

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jupyter-core

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/jupyter_core

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-jupyter_core

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-jupyter-core

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyter_core


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
