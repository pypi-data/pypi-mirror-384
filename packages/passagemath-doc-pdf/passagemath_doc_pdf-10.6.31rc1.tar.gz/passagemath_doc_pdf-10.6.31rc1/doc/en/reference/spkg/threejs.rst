.. _spkg_threejs:

jupyter_threejs_sage: Sage: Open Source Mathematics Software: Jupyter extension for 3D graphics with threejs
============================================================================================================

Description
-----------

Sage: Open Source Mathematics Software: Jupyter extension for 3D graphics with threejs

License
-------

MIT License

Upstream Contact
----------------

https://pypi.org/project/jupyter-threejs-sage/



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

    130

version_requirements.txt::

    jupyter-threejs-sage

See https://repology.org/project/threejs/versions, https://repology.org/project/threejs-sage/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-threejs-sage

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i threejs

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install threejs-sage=122.\*


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
