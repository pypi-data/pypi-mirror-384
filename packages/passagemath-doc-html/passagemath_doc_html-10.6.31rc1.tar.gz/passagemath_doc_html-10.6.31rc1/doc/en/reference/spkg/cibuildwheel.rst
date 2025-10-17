.. _spkg_cibuildwheel:

cibuildwheel: Build Python wheels on CI with minimal configuration
==================================================================

Description
-----------

Build Python wheels on CI with minimal configuration

License
-------

Upstream Contact
----------------

https://pypi.org/project/cibuildwheel/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_certifi`
- :ref:`spkg_filelock`
- :ref:`spkg_packaging`
- :ref:`spkg_platformdirs`

Version Information
-------------------

requirements.txt::

    cibuildwheel==3.1.4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cibuildwheel==3.1.4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cibuildwheel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
