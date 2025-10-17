.. _spkg_schubertpy:

schubertpy: Operations on the Grassmannian: quantum Pieri rules, quantum Giambelli formulae, manipulation of Schubert classes
=============================================================================================================================

Description
-----------

This Python module facilitates operations such as quantum Pieri rules, quantum Giambelli formulae, action and multiplication of Schubert classes, and conversion between different representations of Schubert classes

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/schubertpy/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_gmpy2`
- :ref:`spkg_matplotlib`
- :ref:`spkg_mpmath`
- :ref:`spkg_numpy`
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`
- :ref:`spkg_sympy`

Version Information
-------------------

requirements.txt::

    schubertpy @ git+https://github.com/passagemath/passagemath-pkg-schubertpy.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install schubertpy@git+https://github.com/passagemath/passagemath-pkg-schubertpy.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i schubertpy


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
