.. _spkg_conrey_dirichlet_characters:

conrey_dirichlet_characters: Dirichlet characters using a numbering scheme described by Brian Conrey
====================================================================================================

Description
-----------

Cython code for working with Dirichlet characters
using a numbering scheme described by Brian Conrey.


License
-------

None


Upstream Contact
----------------

- https://github.com/jwbober/conrey-dirichlet-characters
- https://github.com/passagemath/passagemath-pkg-conrey-dirichlet-characters


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_numpy`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_schemes`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    DirichletConrey @ git+https://github.com/passagemath/passagemath-pkg-conrey-dirichlet-characters.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install DirichletConrey@git+https://github.com/passagemath/passagemath-pkg-conrey-dirichlet-characters.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i conrey_dirichlet_characters


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
