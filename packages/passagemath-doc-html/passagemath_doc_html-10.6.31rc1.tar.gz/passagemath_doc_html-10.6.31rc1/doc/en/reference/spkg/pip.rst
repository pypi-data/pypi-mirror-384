.. _spkg_pip:

pip: Tool for installing and managing Python packages
=====================================================

Description
-----------

This package installs pip, the tool for installing and managing Python
packages, such as those found in the Python Package Index. It’s a
replacement for easy_install.

License
-------

MIT


Upstream Contact
----------------

- Project Page: https://github.com/pypa/pip
- Install howto: https://pip.pypa.io/en/latest/installing.html
- Changelog: https://pip.pypa.io/en/latest/news.html
- Bug Tracking: https://github.com/pypa/pip/issues
- Mailing list: http://groups.google.com/group/python-virtualenv
- Docs: https://pip.pypa.io/



Type
----

standard


Dependencies
------------

- $(PYTHON)

Version Information
-------------------

package-version.txt::

    25.0.1

version_requirements.txt::

    pip >=23.1.0

See https://repology.org/project/pip3/versions, https://repology.org/project/python:pip/versions, https://repology.org/project/python3x-pip/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pip\>=23.1.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pip

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pip

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pip

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pip

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pip

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-pip

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pip

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pip

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pip

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pip


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
