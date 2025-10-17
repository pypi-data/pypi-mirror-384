.. _spkg_pari_nflistdata:

pari_nflistdata: PARI data package needed by nflist
===================================================

Description
-----------

PARI package "nflistdata": Needed by nflist to list fields of small discriminant
(currently needed by the single Galois groups A5 and A5(6)) or to list
regular extensions of Q(T) in degree 7 to 15.

License
-------

GPL version 2+


Upstream Contact
----------------

http://pari.math.u-bordeaux.fr/


Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    20220729

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pari_nflistdata


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
