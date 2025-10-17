.. _spkg_stdpairs:

stdpairs: Symbolic computation over a monomial ideal of an affine (non-normal) semigroup ring
=============================================================================================

Description
-----------

Sage library for doing symbolic computation over a monomial ideal of an affine (non-normal) semigroup ring.

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/stdpairs/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_numpy`
- :ref:`spkg_pynormaliz`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_latte_4ti2`
- :ref:`spkg_sagemath_macaulay2`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    stdpairs @ git+https://github.com/byeongsuyu/StdPairs.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install stdpairs@git+https://github.com/byeongsuyu/StdPairs.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i stdpairs


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
