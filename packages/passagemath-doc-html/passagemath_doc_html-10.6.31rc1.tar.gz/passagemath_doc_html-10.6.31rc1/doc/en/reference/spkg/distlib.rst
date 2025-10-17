.. _spkg_distlib:

distlib: Distribution utilities
===============================

Description
-----------

Distribution utilities

License
-------

PSF-2.0

Upstream Contact
----------------

https://pypi.org/project/distlib/



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

    0.3.9

version_requirements.txt::

    distlib

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install distlib

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i distlib

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install distlib

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -python-distlib

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-distlib


If the system package is installed, ``./configure`` will check if it can be used.
