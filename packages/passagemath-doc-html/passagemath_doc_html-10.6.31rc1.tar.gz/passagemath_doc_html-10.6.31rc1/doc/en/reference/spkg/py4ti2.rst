.. _spkg_py4ti2:

py4ti2: Python bindings for 4ti2
================================

Description
-----------

Py4ti2 provides a Python interface to some of the computations performed by 4ti2.


License
-------

GPL v2 or later


Upstream Contact
----------------

https://github.com/alfsan/Py4ti2


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_4ti2`
- :ref:`spkg_glpk`

Version Information
-------------------

package-version.txt::

    0.5.1

version_requirements.txt::

    py4ti2

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install py4ti2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i py4ti2


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
