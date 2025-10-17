.. _spkg_comm:

comm: Jupyter Python Comm implementation, for usage in ipykernel, xeus-python etc.
==================================================================================

Description
-----------

Jupyter Python Comm implementation, for usage in ipykernel, xeus-python etc.

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/comm/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_traitlets`

Version Information
-------------------

package-version.txt::

    0.2.2

version_requirements.txt::

    comm

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install comm

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i comm


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
