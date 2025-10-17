.. _spkg_sagemath_macaulay2_jupyterkernel:

sagemath_macaulay2_jupyterkernel: Jupyter kernel for Macaulay2
==============================================================

Description
-----------

Jupyter kernel for Macaulay2 (passagemath fork)

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/passagemath-macaulay2-jupyterkernel/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ipykernel`
- :ref:`spkg_pexpect`
- :ref:`spkg_sagemath_macaulay2`

Version Information
-------------------

requirements.txt::

    passagemath-macaulay2-jupyterkernel

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-macaulay2-jupyterkernel

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_macaulay2_jupyterkernel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
