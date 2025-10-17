.. _spkg_dependent_bterms:

dependent_bterms: Extension of AsymptoticRing to specify a secondary, dependent (monomially bounded) variable
=============================================================================================================

Description
-----------

Extension to SageMath's module for computations with asymptotic expansions. Provides a special AsymptoticRing that allows to specify a secondary, dependent (monomially bounded) variable

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/dependent-bterms/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    dependent-bterms[passagemath] @ git+https://github.com/passagemath/passagemath-pkg-dependent_bterms.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install dependent-bterms\[passagemath\]@git+https://github.com/passagemath/passagemath-pkg-dependent_bterms.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i dependent_bterms


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
