.. _spkg_sagemath_gap_pkg_jupyterkernel:

sagemath_gap_pkg_jupyterkernel: Native Jupyter kernel for GAP (kernelspec)
==========================================================================

Description
-----------

This is the pip-installed part of the GAP package JupyterKernel.

See also: ``gap_pkg_jupyterkernel``


License
-------

BSD-3-Clause license


Upstream Contact
----------------

- https://pypi.org/project/passagemath-gap-pkg-jupyterkernel/
- https://github.com/gap-packages/JupyterKernel


Type
----

optional


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_gap_pkg_jupyterkernel`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    1.5.1.1

version_requirements.txt::

    passagemath-gap-pkg-jupyterkernel

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gap-pkg-jupyterkernel

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gap_pkg_jupyterkernel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
