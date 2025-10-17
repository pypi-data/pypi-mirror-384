.. _spkg_hypothesis:

hypothesis: A library for property-based testing
================================================

Description
-----------

A library for property-based testing

License
-------

MPL-2.0

Upstream Contact
----------------

https://pypi.org/project/hypothesis/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_attrs`

Version Information
-------------------

requirements.txt::

    hypothesis

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install hypothesis

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i hypothesis


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
