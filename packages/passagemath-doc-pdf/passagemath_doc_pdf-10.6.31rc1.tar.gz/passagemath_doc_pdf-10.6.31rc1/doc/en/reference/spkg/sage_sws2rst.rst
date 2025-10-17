.. _spkg_sage_sws2rst:

sage_sws2rst: Translate legacy Sage worksheet files (.sws) to reStructuredText (.rst) files
===========================================================================================

Description
-----------

Provides a script `sage-sws2rst`, which translates a Sage worksheet file (.sws) into a reStructuredText (.rst) file.

Sage worksheet files (.sws) are a file format that was used by the now-obsolete Sage notebook (https://github.com/sagemath/sagenb), superseded by the Jupyter notebook.  SageNB was dropped in the course of the transition of SageMath to Python 3.

This package was extracted from the SageNB sources in :issue:`28838` to provide a way to convert pedagogical material written available in Sage worksheet format.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_beautifulsoup4`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-sws2rst == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-sws2rst==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sage_sws2rst


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
