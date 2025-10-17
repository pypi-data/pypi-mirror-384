.. _spkg_sagemath_brial:

=================================================================================================
sagemath_brial: Boolean Ring Algebra with BRiAl
=================================================================================================


This pip-installable source distribution ``passagemath-brial`` provides
a Boolean Ring Algebra implementation using binary decision diagrams,
implemented by the BRiAl library, the successor to PolyBoRi.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_brial`
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gmp`
- :ref:`spkg_iml`
- :ref:`spkg_linbox`
- :ref:`spkg_m4ri`
- :ref:`spkg_m4rie`
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

    passagemath-brial == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-brial==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_brial


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
