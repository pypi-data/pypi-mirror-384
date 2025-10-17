.. _spkg_elementary_vectors:

elementary_vectors: SageMath package to work with elementary vectors, sign vectors, oriented matroids and vectors with components in intervals
==============================================================================================================================================

Description
-----------

SageMath package to work with elementary vectors, sign vectors, oriented matroids and vectors with components in intervals

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/elementary-vectors/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    elementary-vectors

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install elementary-vectors

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i elementary_vectors


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
