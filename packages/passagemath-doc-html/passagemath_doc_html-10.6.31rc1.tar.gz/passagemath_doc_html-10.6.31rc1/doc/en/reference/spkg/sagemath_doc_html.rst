.. _spkg_sagemath_doc_html:

sagemath_doc_html: SageMath documentation in HTML format
========================================================

Upon installation, this package builds the SageMath documentation
in HTML format.

It is a standard package.  It is built on every invocation
of ``make`` or ``make all``, but not on ``make build``.
The documentation build can also be run separately using
``make doc-html``.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- $(SAGERUNTIME)
- :ref:`spkg_conway_polynomials`
- :ref:`spkg_elliptic_curves`
- :ref:`spkg_furo`
- :ref:`spkg_graphs`
- :ref:`spkg_jupyter_sphinx`
- :ref:`spkg_mathjax`
- :ref:`spkg_meson_python`
- :ref:`spkg_mpmath`
- :ref:`spkg_pplpy_doc`
- :ref:`spkg_sage_docbuild`
- :ref:`spkg_sagelib`
- :ref:`spkg_sagemath_cliquer`
- :ref:`spkg_sagemath_cmr`
- :ref:`spkg_sagemath_database_cunningham`
- :ref:`spkg_sagemath_database_jones_numfield`
- :ref:`spkg_sagemath_database_kohel`
- :ref:`spkg_sagemath_database_odlyzko_zeta`
- :ref:`spkg_sagemath_database_stein_watkins_mini`
- :ref:`spkg_sagemath_database_symbolic_data`
- :ref:`spkg_sagemath_fricas`
- :ref:`spkg_sagemath_frobby`
- :ref:`spkg_sagemath_gfan`
- :ref:`spkg_sagemath_giac`
- :ref:`spkg_sagemath_kenzo`
- :ref:`spkg_sagemath_latte_4ti2`
- :ref:`spkg_sagemath_msolve`
- :ref:`spkg_sagemath_qepcad`
- :ref:`spkg_sagemath_rankwidth`
- :ref:`spkg_sagemath_rubiks`
- :ref:`spkg_sagemath_sympow`
- :ref:`spkg_sphinx`
- :ref:`spkg_sphinx_copybutton`
- :ref:`spkg_sphinx_inline_tabs`
- :ref:`spkg_sympy`
- :ref:`spkg_tachyon`
- :ref:`spkg_typing_extensions`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-doc-html == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-doc-html==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_doc_html


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
