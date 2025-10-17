.. _spkg_dd_functions:

dd_functions: Differentiably definable (DD-finite) functions
============================================================

Description
-----------

Package to work with differentiably definable functions.

These generalize the class of differentially finite or "D-finite" functions:

- D-finite functions satisfy linear differential equations
  with polynomial coefficients
- DD-finite functions satisfy linear differential equations
  with D-finite functions as coefficients
- differentiably definable functions are obtained by iterating this

License
-------

GPLv3

Upstream Contact
----------------

- https://github.com/Antonio-JP/dd_functions
- https://github.com/passagemath/passagemath-pkg-dd_functions


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ore_algebra`

Version Information
-------------------

requirements.txt::

    dd_functions @ git+https://github.com/passagemath/passagemath-pkg-dd_functions.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install dd_functions@git+https://github.com/passagemath/passagemath-pkg-dd_functions.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i dd_functions


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
