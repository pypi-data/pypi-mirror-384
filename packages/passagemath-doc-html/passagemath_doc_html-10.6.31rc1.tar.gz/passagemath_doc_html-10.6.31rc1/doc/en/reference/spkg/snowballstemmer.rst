.. _spkg_snowballstemmer:

snowballstemmer: Stemmer algorithms for natural language processing in Python
=============================================================================

Description
-----------

This package provides 29 stemmers for 28 languages generated from Snowball algorithms.

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/snowballstemmer/

This is a pure Python stemming library. If PyStemmer is available, this
module uses it to accelerate.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    2.2.0

version_requirements.txt::

    snowballstemmer >=1.2.1

See https://repology.org/project/python:snowballstemmer/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install snowballstemmer\>=1.2.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i snowballstemmer

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install snowballstemmer

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/snowballstemmer

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-snowballstemmer

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-snowballstemmer

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-snowballstemmer


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
