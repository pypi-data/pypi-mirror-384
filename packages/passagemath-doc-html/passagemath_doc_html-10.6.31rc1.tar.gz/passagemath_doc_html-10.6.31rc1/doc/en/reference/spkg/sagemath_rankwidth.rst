.. _spkg_sagemath_rankwidth:

================================================================================================
sagemath_rankwidth: Rankwidth and rank decompositions of graphs with rw
================================================================================================


This pip-installable distribution ``passagemath-rankwidth`` is a small
optional distribution for use with `passagemath-graphs <https://pypi.org/project/passagemath-graphs>`_.

It provides a Cython interface to `rw <https://sourceforge.net/projects/rankwidth/>`_ by
Philipp Klaus Krause, which calculates rank width and rank decompositions.


What is included
----------------

- `Cython interface to rw <https://passagemath.org/docs/latest/html/en/reference/graphs/sage/graphs/graph_decompositions/rankwidth.html>`_


Examples
--------

::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-rankwidth[test]" ipython

    In [1]: from sage.all__sagemath_rankwidth import *

    In [2]: g = graphs.PetersenGraph()

    In [3]: g.rank_decomposition()
    Out[3]: (3, Graph on 19 vertices)


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_rw`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-rankwidth == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-rankwidth==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_rankwidth


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
