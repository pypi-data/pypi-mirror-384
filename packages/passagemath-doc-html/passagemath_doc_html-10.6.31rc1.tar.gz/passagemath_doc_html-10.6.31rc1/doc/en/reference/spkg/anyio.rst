.. _spkg_anyio:

anyio: High level compatibility layer for multiple asynchronous event loop implementations
==========================================================================================

Description
-----------

High level compatibility layer for multiple asynchronous event loop implementations

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/anyio/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_exceptiongroup`
- :ref:`spkg_idna`
- :ref:`spkg_pip`
- :ref:`spkg_sniffio`
- :ref:`spkg_typing_extensions`

Version Information
-------------------

package-version.txt::

    4.9.0

version_requirements.txt::

    anyio

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install anyio

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i anyio


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
