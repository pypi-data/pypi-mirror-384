.. _spkg_tides:

tides: Integration of ODEs
==========================

Description
-----------

TIDES is a library for integration of ODEs with high precision.

License
-------

GPLv3+


Upstream Contact
----------------

-  Marcos Rodriguez (marcos@unizar.es)

Dependencies
------------

-  gcc
-  mpfr
-  gmp


Special Update/Build Instructions
---------------------------------

minc_tides.patch changes the size of the name of the temporal files, so
there is no problem in systems that use long names. Also solves a bug in
the inverse function.


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_mpfr`

Version Information
-------------------

package-version.txt::

    2.0.p0

See https://repology.org/project/tides/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i tides


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
