.. _spkg_pplitepy:

pplitepy: Python pplite wrapper
===============================

Description
-----------

Python pplite wrapper

License
-------

GPL v3

Upstream Contact
----------------

https://pypi.org/project/pplitepy/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_flint`
- :ref:`spkg_pplite`

Version Information
-------------------

requirements.txt::

    pplitepy

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pplitepy

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pplitepy


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
