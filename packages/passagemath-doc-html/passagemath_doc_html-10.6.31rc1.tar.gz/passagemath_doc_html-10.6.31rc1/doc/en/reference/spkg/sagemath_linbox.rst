.. _spkg_sagemath_linbox:

=======================================================================================================================
sagemath_linbox: Linear Algebra with Givaro, fflas-ffpack, LinBox, IML, m4ri(e)
=======================================================================================================================


This pip-installable distribution ``passagemath-linbox``
provides modules that depend on the `LinBox suite <https://linalg.org/>`_
(Givaro, fflas-ffpack, LinBox), or on the libraries
`IML <https://cs.uwaterloo.ca/~astorjoh/iml.html>`_,
`m4ri <https://bitbucket.org/malb/m4ri/src/master/>`_,
`m4rie <https://bitbucket.org/malb/m4rie/src/master/>`_.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_givaro`
- :ref:`spkg_gmp`
- :ref:`spkg_iml`
- :ref:`spkg_linbox`
- :ref:`spkg_m4ri`
- :ref:`spkg_m4rie`
- :ref:`spkg_memory_allocator`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_numpy`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-linbox == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-linbox==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_linbox


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
