.. _spkg_sagemath_glucose:

=======================================================================================================
sagemath_glucose: Interface to the SAT solver glucose
=======================================================================================================


This pip-installable distribution ``passagemath-glucose`` provides an interface
to the SAT solver `glucose <http://www.labri.fr/perso/lsimon/glucose/>`_.


What is included
----------------

* Binary wheels on PyPI contain prebuilt copies of glucose executables.


Examples
--------

Using glucose programs on the command line::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-glucose" sage -sh -c glucose

Finding the installation location of a glucose program::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-glucose[test]" ipython

    In [1]: from sage.features.sat import Glucose

    In [2]: Glucose().absolute_filename()
    Out[2]: '.../bin/glucose'

Use with `sage.sat <https://passagemath.org/docs/latest/html/en/reference/sat/index.html>`_::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-glucose[test]" ipython

    In [1]: from sage.all__sagemath_glucose import *

    In [2]: from sage.sat.solvers.dimacs import Glucose

    In [3]: solver = Glucose(); solver.add_clause((1,2)); solver.add_clause((-1,2)); solver.add_clause((1,-2))

    In [4]: solver()
    Out[4]: (None, True, True)


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_glucose`
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

    passagemath-glucose == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-glucose==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_glucose


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
