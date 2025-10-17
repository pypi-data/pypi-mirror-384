.. _spkg_sagemath_msolve:

====================================================================================================
sagemath_msolve: Polynomial system solving through algebraic methods with msolve
====================================================================================================


This pip-installable distribution ``passagemath-msolve`` provides an interface to `msolve <https://msolve.lip6.fr/>`_, which implements computer algebra algorithms for solving polynomial systems (with rational coefficients or coefficients in a prime field).


Examples
--------

A quick way to try it out interactively::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-msolve[test]" ipython

    In [1]: from sage.all__sagemath_msolve import *

    In [2]: R = PolynomialRing(QQ, 2, names=['x', 'y'], order='lex')

    In [3]: x, y = R.gens()

    In [4]: I = Ideal([ x*y - 1, (x-2)**2 + (y-1)**2 - 1])

    In [5]: I.variety(RBF, algorithm='msolve', proof=False)
    Out[5]:
    [{x: [2.76929235423863 +/- 2.08e-15], y: [0.361103080528647 +/- 4.53e-16]},
     {x: 1.000000000000000, y: 1.000000000000000}]


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gmp`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_msolve`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_objects`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-msolve == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-msolve==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_msolve


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
