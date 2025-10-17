.. _spkg_msinvar:

msinvar: Package for computing various moduli space invariants
==============================================================

Description
-----------

This is a Sage package for computing various moduli space invariants.

License
-------

GPLv2

Upstream Contact
----------------

- https://github.com/smzg/msinvar
- https://github.com/passagemath/passagemath-pkg-msinvar


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_singular`

Version Information
-------------------

requirements.txt::

    msinvar @ git+https://github.com/passagemath/passagemath-pkg-msinvar.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install msinvar@git+https://github.com/passagemath/passagemath-pkg-msinvar.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i msinvar


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
