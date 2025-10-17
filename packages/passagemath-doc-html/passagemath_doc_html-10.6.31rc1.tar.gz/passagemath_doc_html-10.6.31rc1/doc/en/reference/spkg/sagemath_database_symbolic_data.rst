.. _spkg_sagemath_database_symbolic_data:

=============================================================================
sagemath_database_symbolic_data: Database from the SymbolicData project
=============================================================================


This pip-installable distribution ``passagemath-database-symbolic-data`` is a
distribution of the database from the SymbolicData project.


What is included
----------------

- Wheels on PyPI include the database_symbolic_data files


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_database_symbolic_data`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-database-symbolic-data == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-database-symbolic-data==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_database_symbolic_data


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
