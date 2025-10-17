.. _spkg_lefschetz_family:

lefschetz_family: Computing periods of algebraic varieties using Lefschetz fibration theory
===========================================================================================

Description
-----------

This package implements algorithms relying on Lefschetz fibration theory to compute periods of algebraic varieties.

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/lefschetz-family/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ore_algebra`
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_schemes`
- :ref:`spkg_sagemath_symbolics`
- :ref:`spkg_scipy`

Version Information
-------------------

requirements.txt::

    lefschetz-family

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install lefschetz-family

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i lefschetz_family


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
