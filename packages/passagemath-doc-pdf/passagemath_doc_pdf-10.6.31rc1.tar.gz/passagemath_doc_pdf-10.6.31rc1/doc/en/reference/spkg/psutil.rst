.. _spkg_psutil:

psutil: Cross-platform lib for process and system monitoring in Python.
=======================================================================

Description
-----------

Cross-platform lib for process and system monitoring in Python.

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/psutil/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    7.0.0

version_requirements.txt::

    psutil

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install psutil

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i psutil


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
