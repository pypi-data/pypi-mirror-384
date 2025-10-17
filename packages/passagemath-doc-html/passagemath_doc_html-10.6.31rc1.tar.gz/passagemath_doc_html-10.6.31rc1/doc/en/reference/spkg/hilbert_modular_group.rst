.. _spkg_hilbert_modular_group:

hilbert_modular_group: Algorithms for Hilbert modular groups
============================================================

Description
-----------

Algorithms for Hilbert modular groups

License
-------

GPL v3

Upstream Contact
----------------

https://pypi.org/project/hilbert-modular-group/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_sagelib`

Version Information
-------------------

requirements.txt::

    hilbert-modular-group

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install hilbert-modular-group

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i hilbert_modular_group


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
