.. _spkg_multipolynomial_bases:

multipolynomial_bases: Sage implementation for bases of multipolynomials
========================================================================

Description
-----------

Sage implementation for bases of multipolynomials

License
-------

GPLv2

Upstream Contact
----------------

- https://pypi.org/project/multipolynomial-bases/
- https://github.com/passagemath/passagemath-pkg-multipolynomial-bases


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    multipolynomial-bases @ git+https://github.com/passagemath/passagemath-pkg-multipolynomial-bases.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install multipolynomial-bases@git+https://github.com/passagemath/passagemath-pkg-multipolynomial-bases.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i multipolynomial_bases


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
