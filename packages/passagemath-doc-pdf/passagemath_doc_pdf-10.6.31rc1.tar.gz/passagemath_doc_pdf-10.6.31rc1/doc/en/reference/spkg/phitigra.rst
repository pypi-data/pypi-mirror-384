.. _spkg_phitigra:

phitigra: Graph editor for SageMath/Jupyter
===========================================

Description
-----------

Graph editor for SageMath/Jupyter

License
-------

Upstream Contact
----------------

https://pypi.org/project/phitigra/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ipywidgets`
- :ref:`spkg_numpy`
- :ref:`spkg_pillow`

Version Information
-------------------

requirements.txt::

    phitigra>=0.2.6

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install phitigra\>=0.2.6

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i phitigra


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
