.. _spkg_cffi:

cffi: Foreign Function Interface for Python calling C code
==========================================================

Description
-----------

development website: https://foss.heptapod.net/pypy/cffi

documentation website: https://cffi.readthedocs.io/en/latest/

PyPI page: https://pypi.org/project/cffi/

License
-------

MIT

Upstream Contact
----------------

https://foss.heptapod.net/pypy/cffi


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pycparser`

Version Information
-------------------

package-version.txt::

    1.17.1

version_requirements.txt::

    cffi >=1.14.0

See https://repology.org/project/python:cffi/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cffi\>=1.14.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cffi

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cffi

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-cffi

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge virtual/python-cffi

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install cffi

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-cffi

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-cffi

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-cffi


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
