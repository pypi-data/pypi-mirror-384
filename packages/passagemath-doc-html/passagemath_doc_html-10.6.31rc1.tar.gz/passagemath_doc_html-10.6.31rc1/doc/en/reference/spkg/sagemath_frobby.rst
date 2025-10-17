.. _spkg_sagemath_frobby:

================================================================================
sagemath_frobby: Computations on monomial ideals with Frobby
================================================================================


This pip-installable source distribution ``passagemath-frobby`` provides an interface to Frobby,
the package for computations on monomial ideals.


Examples
--------

A quick way to try it out interactively::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-frobby[test]" ipython

    In [1]: from sage.all__sagemath_frobby import *


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_frobby`
- :ref:`spkg_gmp`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_objects`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-frobby == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-frobby==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_frobby


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
