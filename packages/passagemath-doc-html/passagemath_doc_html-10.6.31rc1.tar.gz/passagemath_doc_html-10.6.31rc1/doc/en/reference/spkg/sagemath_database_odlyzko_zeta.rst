.. _spkg_sagemath_database_odlyzko_zeta:

==================================================================================
sagemath_database_odlyzko_zeta: Table of zeros of the Riemann zeta function
==================================================================================


This pip-installable distribution ``passagemath-database-odlyzko-zeta`` is a
distribution of data, a table of zeros of the Riemann zeta function
by Andrew Odlyzko.

This package contains the file 'zeros6' with the first 2,001,052 zeros
of the Riemann zeta function, accurate to within 4*10^(-9).


What is included
----------------

- Wheels on PyPI include the database_odlyzko_zeta files


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_database_odlyzko_zeta`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-database-odlyzko-zeta == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-database-odlyzko-zeta==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_database_odlyzko_zeta


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
