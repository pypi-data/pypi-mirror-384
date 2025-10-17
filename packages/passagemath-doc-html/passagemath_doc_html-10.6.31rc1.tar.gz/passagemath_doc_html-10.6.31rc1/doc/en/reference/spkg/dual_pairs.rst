.. _spkg_dual_pairs:

dual_pairs: Computing with dual pairs of algebras
=================================================

License
-------

GPL 3


Upstream Contact
----------------

- https://github.com/passagemath/passagemath-pkg-dual-pairs
- https://gitlab.com/pbruin/dual-pairs


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_pari_galdata`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_schemes`
- :ref:`spkg_sagemath_singular`

Version Information
-------------------

requirements.txt::

    dual_pairs @ git+https://github.com/passagemath/passagemath-pkg-dual-pairs

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install dual_pairs@git+https://github.com/passagemath/passagemath-pkg-dual-pairs

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i dual_pairs


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
