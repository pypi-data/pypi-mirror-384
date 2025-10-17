.. _spkg_sagemath_tdlib:

================================================================================================
sagemath_tdlib: Tree decompositions with tdlib
================================================================================================


This pip-installable distribution ``passagemath-tdlib`` is a small optional distribution for use with `passagemath-graphs <https://pypi.org/project/passagemath-graphs>`_.

It provides a Cython interface to the ``tdlib`` library, now also known as `treedec <https://gitlab.com/freetdi/treedec>`_, providing
algorithms concerning tree decompositions.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`
- :ref:`spkg_tdlib`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-tdlib == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-tdlib==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_tdlib


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
