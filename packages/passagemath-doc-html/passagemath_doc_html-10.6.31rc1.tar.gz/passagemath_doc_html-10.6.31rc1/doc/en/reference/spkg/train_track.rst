.. _spkg_train_track:

train_track: Train-tracks for freegroup automorphisms
=====================================================

Description
-----------

Train-tracks for freegroup automorphisms

License
-------

GPLv3.0

Upstream Contact
----------------

https://pypi.org/project/train-track/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    train-track @ git+https://github.com/coulbois/sage-train-track.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install train-track@git+https://github.com/coulbois/sage-train-track.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i train_track


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
