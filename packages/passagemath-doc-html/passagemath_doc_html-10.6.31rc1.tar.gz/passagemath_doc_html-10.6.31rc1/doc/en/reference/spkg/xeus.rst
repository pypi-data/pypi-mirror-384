.. _spkg_xeus:

xeus: C++ implementation of the Jupyter Kernel protocol
=======================================================

Description
-----------

xeus is a library meant to facilitate the implementation of kernels for Jupyter.


License
-------

BSD-3-Clause license


Upstream Contact
----------------

https://github.com/jupyter-xeus/xeus


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_libuuid`
- :ref:`spkg_ninja_build`
- :ref:`spkg_nlohmann_json`

Version Information
-------------------

package-version.txt::

    5.2.3

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i xeus


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
