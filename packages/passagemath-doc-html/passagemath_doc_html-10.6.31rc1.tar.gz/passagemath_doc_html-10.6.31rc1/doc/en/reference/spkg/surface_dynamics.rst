.. _spkg_surface_dynamics:

surface_dynamics: dynamics on surfaces (measured foliations, interval exchange transformation, Teichmüller flow, etc)
======================================================================================================================

Description
-----------

Dynamics on surfaces.

License
-------

GPLv2+

Upstream Contact
----------------

https://gitlab.com/videlec/surface_dynamics
https://pypi.org/project/surface-dynamics/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- $(SAGERUNTIME)
- :ref:`spkg_cysignals`
- :ref:`spkg_pplpy`

Version Information
-------------------

requirements.txt::

    surface_dynamics

See https://repology.org/project/python:surface-dynamics/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install surface_dynamics

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i surface_dynamics


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
