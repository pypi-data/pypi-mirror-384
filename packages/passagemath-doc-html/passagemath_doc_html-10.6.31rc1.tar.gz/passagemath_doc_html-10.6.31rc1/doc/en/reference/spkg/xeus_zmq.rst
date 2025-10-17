.. _spkg_xeus_zmq:

xeus_zmq: ZeroMQ-based middleware for xeus
==========================================

Description
-----------

xeus-zmq provides various implementations of the xserver API from xeus, based on the ZeroMQ library.


License
-------

BSD-3-Clause license


Upstream Contact
----------------

https://github.com/jupyter-xeus/xeus-zmq


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_cppzmq`
- :ref:`spkg_ninja_build`
- :ref:`spkg_nlohmann_json`
- :ref:`spkg_openssl`
- :ref:`spkg_xeus`
- :ref:`spkg_zeromq`

Version Information
-------------------

package-version.txt::

    3.1.0

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i xeus_zmq


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
