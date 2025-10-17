.. _spkg_admcycles:

admcycles: Computation in the tautological ring of the moduli space of curves
==============================================================================

Description
-----------

The SageMath package admcycles offers the possibility to compute in the
tautological ring of the Deligne-Mumford compactification of the moduli space
of curves. Construction for standard generators are provided (psi, kappa and
lambda classes) as well as more advanced algebraic construction (double
ramification cycle, strata of differentials).

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/admcycles/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_primecountpy`
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`
- :ref:`spkg_sympy`

Version Information
-------------------

requirements.txt::

    admcycles @ git+https://gitlab.com/modulispaces/admcycles.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install admcycles@git+https://gitlab.com/modulispaces/admcycles.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i admcycles


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
