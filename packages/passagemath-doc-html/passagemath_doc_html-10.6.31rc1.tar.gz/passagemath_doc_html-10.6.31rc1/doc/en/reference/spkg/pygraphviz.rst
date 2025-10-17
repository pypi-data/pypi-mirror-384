.. _spkg_pygraphviz:

pygraphviz: Python interface to Graphviz
========================================

Description
-----------

Python interface to Graphviz

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/pygraphviz/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_libgraphviz`

Version Information
-------------------

requirements.txt::

    pygraphviz

version_requirements.txt::

    pygraphviz

See https://repology.org/project/python:pygraphviz/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pygraphviz

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pygraphviz

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pygraphviz

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pygraphviz

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pygraphviz


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
