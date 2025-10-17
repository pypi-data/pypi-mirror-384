.. _spkg_circkit:

circkit: Circuit toolkit mainly for cryptographic usage
=======================================================

Description
-----------

Circuit toolkit mainly for cryptographic usage

License
-------

MIT

Upstream Contact
----------------

- https://pypi.org/project/circkit/
- https://github.com/passagemath/passagemath-pkg-circkit


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_pari`

Version Information
-------------------

requirements.txt::

    circkit @ git+https://github.com/passagemath/passagemath-pkg-circkit.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install circkit@git+https://github.com/passagemath/passagemath-pkg-circkit.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i circkit


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
