.. _spkg_sagemath_pari_galpol:

===================================================================================================================================
sagemath_pari_galpol: Computational Number Theory with PARI/GP: Database of polynomials defining Galois extensions
===================================================================================================================================


This pip-installable distribution ``passagemath-pari-galpol`` is a
distribution of data for use with ``passagemath-pari``.


What is included
----------------

- Wheels on PyPI include the galpol files


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pari_galpol`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-pari-galpol == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-pari-galpol==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_pari_galpol


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
