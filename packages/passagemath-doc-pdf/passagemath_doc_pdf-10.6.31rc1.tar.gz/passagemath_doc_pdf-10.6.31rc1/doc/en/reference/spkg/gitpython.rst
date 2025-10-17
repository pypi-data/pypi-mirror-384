.. _spkg_gitpython:

gitpython: GitPython is a python library used to interact with Git repositories
===============================================================================

Description
-----------

GitPython is a python library used to interact with Git repositories

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/GitPython/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

requirements.txt::

    GitPython

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install GitPython

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gitpython


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
