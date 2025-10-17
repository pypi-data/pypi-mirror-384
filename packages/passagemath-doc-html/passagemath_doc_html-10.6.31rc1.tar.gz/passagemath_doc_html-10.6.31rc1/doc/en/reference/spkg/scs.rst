.. _spkg_scs:

scs: Splitting conic solver
===========================

Description
-----------

scs: splitting conic solver

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/scs/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cmake`
- :ref:`spkg_numpy`

Version Information
-------------------

package-version.txt::

    3.2.7

version_requirements.txt::

    scs

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install scs

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i scs

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install scs


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
