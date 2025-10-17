.. _spkg_sagemath_gfan:

===================================================================================
sagemath_gfan: Groebner fans and tropical varieties with gfan
===================================================================================


This pip-installable distribution ``passagemath-gfan`` provides an interface to
`gfan <https://users-math.au.dk/jensen/software/gfan/gfan.html>`_, the package for
Groebner fans and tropical varieties.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gfan`
- :ref:`spkg_gmp`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-gfan == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gfan==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gfan


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
