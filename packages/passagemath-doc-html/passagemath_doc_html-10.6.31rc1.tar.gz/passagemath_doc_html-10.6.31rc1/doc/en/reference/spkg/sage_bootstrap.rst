.. _spkg_sage_bootstrap:

sage_bootstrap: System package database with support for PURLs (package URLs)
==================================================================================================


This distribution package ``passagemath-bootstrap`` provides:

- a script ``sage-guess-package-system``::

    $ sage-guess-package-system
    homebrew

- a script ``sage-get-system-packages`` to map PURLs to names of system packages::

    $ sage-get-system-packages gentoo generic/gmp generic/gap
    sci-mathematics/gap
    dev-libs/gmp

- a script ``sage-print-system-package-command`` to print system package installation
  commands for given PURLs::

    $ sage-print-system-package-command void --spkg install generic/gmp generic/gap
    xbps-install gmp-devel gmpxx-devel

    $ sage-print-system-package-command fedora --spkg --sudo install generic/linbox
    sudo dnf install linbox linbox-devel

- a script ``sage-package`` to query the system package database::

    $ sage-package properties generic/gmp
    path:                        .../site-packages/sage_root/build/pkgs/gmp
    version_with_patchlevel:     6.3.0
    type:                        standard
    source:                      normal
    trees:                       SAGE_LOCAL
    purl:                        pkg:generic/gmp
    description:                 Library for arbitrary precision arithmetic
    uses_python_package_check:   False

- a script ``sage-spkg-info`` to print system package information::

    $ sage-spkg-info generic/macaulay2
    ...

    $ sage-spkg-info pypi/setuptools
    ...

- a Python API defined in ``sage_bootstrap``

The database of packages is included with ``passagemath-bootstrap`` and consists of
over 600 packages; see https://passagemath.org/docs/latest/html/en/reference/spkg/index.html
for a list of the available packages.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc1

version_requirements.txt::

    passagemath-bootstrap == 10.6.31rc1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-bootstrap==10.6.31rc1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sage_bootstrap


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
