.. _spkg_nlohmann_json:

nlohmann_json: JSON for modern C++
==================================

Description
-----------

JSON library


License
-------

MIT


Upstream Contact
----------------

https://github.com/nlohmann/json


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`

Version Information
-------------------

package-version.txt::

    3.12.0

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i nlohmann_json


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
