.. _spkg_mclf:

mclf: Computing with Models of Curves over Local Fields
=======================================================

Description
-----------

Sage toolbox for computing with Models of Curves over Local Fields

License
-------

GPLv2

Upstream Contact
----------------

- https://pypi.org/project/mclf/
- https://github.com/passagemath/passagemath-pkg-mclf


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_singular`

Version Information
-------------------

requirements.txt::

    mclf @ git+https://github.com/passagemath/passagemath-pkg-mclf.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install mclf@git+https://github.com/passagemath/passagemath-pkg-mclf.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i mclf


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
