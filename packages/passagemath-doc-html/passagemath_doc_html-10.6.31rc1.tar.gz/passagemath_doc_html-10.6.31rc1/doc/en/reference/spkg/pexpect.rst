.. _spkg_pexpect:

pexpect: Python module for controlling and automating other programs
====================================================================

Description
-----------

Pexpect is a pure Python module for spawning child applications;
controlling them; and responding to expected patterns in their output.

License
-------

ISC license: http://opensource.org/licenses/isc-license.txt This license
is approved by the OSI and FSF as GPL-compatible.


Upstream Contact
----------------

- http://pexpect.readthedocs.org/en/stable/
- https://github.com/pexpect/pexpect



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ptyprocess`

Version Information
-------------------

package-version.txt::

    4.9.0

src/pyproject.toml::

    pexpect >=4.8.0

version_requirements.txt::

    pexpect

See https://repology.org/project/pexpect/versions, https://repology.org/project/python:pexpect/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pexpect\>=4.8.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pexpect

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pexpect

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pexpect

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pexpect

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install misc/py-pexpect

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pexpect

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pexpect

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pexpect

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pexpect


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
