.. _spkg_scikit_build_core:

scikit_build_core: Build backend for CMake based projects
=========================================================

Description
-----------

Build backend for CMake based projects

License
-------

Upstream Contact
----------------

https://pypi.org/project/scikit-build-core/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_exceptiongroup`
- :ref:`spkg_packaging`
- :ref:`spkg_pathspec`
- :ref:`spkg_pip`
- :ref:`spkg_tomli`
- :ref:`spkg_typing_extensions`

Version Information
-------------------

package-version.txt::

    0.11.3

version_requirements.txt::

    scikit-build-core

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install scikit-build-core

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i scikit_build_core


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
