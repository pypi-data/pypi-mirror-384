.. _spkg_snappy:

snappy: Topology and geometry of 3-manifolds, with a focus on hyperbolic structures
===================================================================================

Description
-----------

Studying the topology and geometry of 3-manifolds, with a focus on hyperbolic structures.

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/snappy/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_decorator`
- :ref:`spkg_ipython`
- :ref:`spkg_sagelib`
- :ref:`spkg_sagemath_pari`

Version Information
-------------------

requirements.txt::

    snappy
    cypari !=2.4.0
    snappy_15_knots

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install snappy cypari\!=2.4.0 snappy_15_knots

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i snappy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
