.. _spkg_cutgeneratingfunctionology:

cutgeneratingfunctionology: Python code for computation and experimentation with cut-generating functions
=========================================================================================================

Description
-----------

Python code for computation and experimentation with cut-generating functions

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/cutgeneratingfunctionology/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_singular`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    cutgeneratingfunctionology

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cutgeneratingfunctionology

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cutgeneratingfunctionology


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
