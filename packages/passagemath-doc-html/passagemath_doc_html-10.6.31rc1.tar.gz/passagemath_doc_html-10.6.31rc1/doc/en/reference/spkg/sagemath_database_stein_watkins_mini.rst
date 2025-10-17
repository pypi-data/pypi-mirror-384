.. _spkg_sagemath_database_stein_watkins_mini:

====================================================================================================
sagemath_database_stein_watkins_mini: The Stein-Watkins database of elliptic curves (small version)
====================================================================================================


This pip-installable distribution ``passagemath-database-stein-watkins-mini`` is a
distribution of data for use with ``passagemath-schemes``.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_database_stein_watkins_mini`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-database-stein-watkins-mini == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-database-stein-watkins-mini==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_database_stein_watkins_mini


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
