.. _spkg_sagemath_mcqd:

===================================================================================================
sagemath_mcqd: Finding maximum cliques with mcqd
===================================================================================================


This pip-installable distribution ``passagemath-mcqd`` is a small
optional distribution for use with ``passagemath-standard``.

It provides a Cython interface to the ``mcqd`` library,
providing a fast exact algorithm for finding a maximum clique in
an undirected graph.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_mcqd`
- :ref:`spkg_memory_allocator`
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

    passagemath-mcqd == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-mcqd==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_mcqd


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
