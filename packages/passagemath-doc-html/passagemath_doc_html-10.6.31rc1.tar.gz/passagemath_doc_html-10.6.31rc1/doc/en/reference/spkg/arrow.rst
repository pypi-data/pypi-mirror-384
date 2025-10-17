.. _spkg_arrow:

arrow: Better dates & times for Python
======================================

Description
-----------

Better dates & times for Python

License
-------

Apache 2.0

Upstream Contact
----------------

https://pypi.org/project/arrow/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_dateutil`
- :ref:`spkg_pip`
- :ref:`spkg_types_python_dateutil`

Version Information
-------------------

package-version.txt::

    1.3.0

version_requirements.txt::

    arrow

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install arrow

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i arrow


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
