.. _spkg_stallings_graphs:

stallings_graphs: Stallings graph representation of finitely generated subgroups of free groups
===============================================================================================

Description
-----------

Stallings graph representation of finitely generated subgroups of free groups

License
-------

GPLv2+

Upstream Contact
----------------

- https://pypi.org/project/stallings-graphs/
- https://github.com/passagemath/passagemath-pkg-stallings_graphs


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_slabbe`
- :ref:`spkg_train_track`

Version Information
-------------------

requirements.txt::

    stallings-graphs @ git+https://github.com/passagemath/passagemath-pkg-stallings_graphs.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install stallings-graphs@git+https://github.com/passagemath/passagemath-pkg-stallings_graphs.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i stallings_graphs


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
