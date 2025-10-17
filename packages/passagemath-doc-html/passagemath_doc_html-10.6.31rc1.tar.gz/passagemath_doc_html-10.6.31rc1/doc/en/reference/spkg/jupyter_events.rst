.. _spkg_jupyter_events:

jupyter_events: Jupyter Event System library
============================================

Description
-----------

Jupyter Event System library

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/jupyter-events/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_jsonschema`
- :ref:`spkg_pip`
- :ref:`spkg_python_json_logger`
- :ref:`spkg_pyyaml`
- :ref:`spkg_referencing`
- :ref:`spkg_rfc3339_validator`
- :ref:`spkg_rfc3986_validator`

Version Information
-------------------

package-version.txt::

    0.6.3

version_requirements.txt::

    jupyter-events

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-events

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_events


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
