.. _spkg_hodge_diamond_cutter:

hodge_diamond_cutter: Compute and manipulate Hodge diamonds for many classes of smooth projective varieties
===========================================================================================================

Description
-----------

A collection of Python classes and functions in Sage to deal with Hodge diamonds
(and Hochschild homology) of smooth projective varieties, together with many
constructions.


License
-------

GPL v3


Upstream Contact
----------------

- https://github.com/pbelmans/hodge-diamond-cutter
- https://github.com/passagemath/passagemath-pkg-hodge-diamond-cutter


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_singular`

Version Information
-------------------

requirements.txt::

    diamond @ git+https://github.com/passagemath/passagemath-pkg-hodge-diamond-cutter.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install diamond@git+https://github.com/passagemath/passagemath-pkg-hodge-diamond-cutter.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i hodge_diamond_cutter


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
