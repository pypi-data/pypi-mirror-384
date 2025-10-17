.. _spkg_cppzmq:

cppzmq: Header-only C++ binding for libzmq
==========================================

Description
-----------

C++ binding for libzmq


License
-------

MIT


Upstream Contact
----------------

https://github.com/zeromq/cppzmq


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`
- :ref:`spkg_zeromq`

Version Information
-------------------

package-version.txt::

    4.11.0

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cppzmq


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
