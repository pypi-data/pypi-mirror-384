.. _spkg_jupyter_lsp:

jupyter_lsp: Multi-Language Server WebSocket proxy for Jupyter Notebook/Lab server
==================================================================================

Description
-----------

Multi-Language Server WebSocket proxy for Jupyter Notebook/Lab server

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/jupyter-lsp/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_jupyter_server`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    2.2.5

version_requirements.txt::

    jupyter-lsp

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-lsp

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_lsp


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
