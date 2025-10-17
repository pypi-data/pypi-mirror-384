.. _spkg_sage_numerical_backends_cplex:

sage_numerical_backends_cplex: Cplex backend for Sage MixedIntegerLinearProgram
===============================================================================

Description
-----------

Cplex backend for Sage MixedIntegerLinearProgram

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/passagemath-cplex/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- $(SAGERUNTIME)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_ipywidgets`

Version Information
-------------------

package-version.txt::

    10.4.1

version_requirements.txt::

    passagemath-cplex

See https://repology.org/project/python:sage-numerical-backends-cplex/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-cplex

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sage_numerical_backends_cplex


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
