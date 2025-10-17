.. _spkg_dateutil:

dateutil: Extensions to the standard Python module datetime
===========================================================

Description
-----------

The dateutil module provides powerful extensions to the standard
datetime module.

License
-------

Simplified BSD License


Upstream Contact
----------------

Author: Gustavo Niemeyer <gustavo@niemeyer.net>

Home page: http://labix.org/python-dateutil

https://pypi.org/project/python-dateutil/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`
- :ref:`spkg_six`

Version Information
-------------------

package-version.txt::

    2.9.0.post0

version_requirements.txt::

    python-dateutil >=2.8.1

See https://repology.org/project/python:python-dateutil/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install python-dateutil\>=2.8.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i dateutil

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-dateutil

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install python-dateutil

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-dateutil

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-dateutil

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-dateutil

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/python-dateutil

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-dateutil

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-python-dateutil

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-dateutil


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
