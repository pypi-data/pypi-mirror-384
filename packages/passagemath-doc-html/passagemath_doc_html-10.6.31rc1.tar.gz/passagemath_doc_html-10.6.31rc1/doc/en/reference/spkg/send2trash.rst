.. _spkg_send2trash:

send2trash: Send file to trash natively under Mac OS X, Windows and Linux
=========================================================================

Description
-----------

Send file to trash natively under Mac OS X, Windows and Linux.

License
-------

BSD License

Upstream Contact
----------------

https://pypi.org/project/Send2Trash/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    1.8.3

version_requirements.txt::

    send2trash >=1.5.0

See https://repology.org/project/send2trash/versions, https://repology.org/project/python:send2trash/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install send2trash\>=1.5.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i send2trash

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install send2trash

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-send2trash

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/send2trash

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-send2trash

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-Send2Trash

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-send2trash


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
