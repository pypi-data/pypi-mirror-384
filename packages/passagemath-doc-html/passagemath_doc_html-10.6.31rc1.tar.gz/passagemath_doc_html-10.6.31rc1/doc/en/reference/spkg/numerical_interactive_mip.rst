.. _spkg_numerical_interactive_mip:

numerical_interactive_mip: Interactive mixed integer linear programming solver
==============================================================================

Description
-----------

Interactive mixed integer linear programming solver

License
-------

GNU General Public License (GPL) v2 or later

Upstream Contact
----------------

https://pypi.org/project/sage-numerical-interactive-mip/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    sage-numerical-interactive-mip

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sage-numerical-interactive-mip

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i numerical_interactive_mip


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
