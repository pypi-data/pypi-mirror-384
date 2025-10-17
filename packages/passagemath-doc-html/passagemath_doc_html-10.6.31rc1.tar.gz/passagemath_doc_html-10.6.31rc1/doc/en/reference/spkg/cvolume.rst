.. _spkg_cvolume:

cvolume: Completed and Masur-Veech volumes of strata of quadratic differentials with odd zeros
==============================================================================================

Description
-----------

cvolume is a SageMath module to compute completed and Masur-Veech volumes of strata
of quadratic differentials with odd zeros.

License
-------

GPLv2+

Upstream Contact
----------------

- https://github.com/eduryev/cvolume
- https://github.com/passagemath/passagemath-pkg-cvolume


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_admcycles`

Version Information
-------------------

requirements.txt::

    cvolume @ git+https://github.com/passagemath/passagemath-pkg-cvolume.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cvolume@git+https://github.com/passagemath/passagemath-pkg-cvolume.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cvolume


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
