.. _spkg_abelfunctions:

abelfunctions: Computing with Abelian functions, Riemann surfaces, and algebraic curves
=======================================================================================

Description
-----------

A Sage library for computing with Abelian functions, Riemann surfaces, and algebraic curves.

License
-------

MIT

Upstream Contact
----------------

https://github.com/abelfunctions/abelfunctions


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_networkx`
- :ref:`spkg_numpy`
- :ref:`spkg_pythran`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`
- :ref:`spkg_scipy`
- :ref:`spkg_sympy`

Version Information
-------------------

requirements.txt::

    abelfunctions @ git+https://github.com/abelfunctions/abelfunctions.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install abelfunctions@git+https://github.com/abelfunctions/abelfunctions.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i abelfunctions


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
