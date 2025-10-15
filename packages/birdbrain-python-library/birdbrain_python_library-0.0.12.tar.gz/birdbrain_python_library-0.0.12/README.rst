========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |github-actions| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/BirdBrain-Python-Library/badge/?style=flat
    :target: https://BirdBrain-Python-Library.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/fmorton/BirdBrain-Python-Library/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/fmorton/BirdBrain-Python-Library/actions

.. |requires| image:: https://requires.io/github/fmorton/BirdBrain-Python-Library/requirements.svg?branch=main
    :alt: Requirements Status
    :target: https://requires.io/github/fmorton/BirdBrain-Python-Library/requirements/?branch=main

.. |codecov| image:: https://codecov.io/gh/fmorton/BirdBrain-Python-Library/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://codecov.io/github/fmorton/BirdBrain-Python-Library

.. |version| image:: https://img.shields.io/pypi/v/birdbrain-python-library.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/birdbrain-python-library

.. |wheel| image:: https://img.shields.io/pypi/wheel/birdbrain-python-library.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/birdbrain-python-library

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/birdbrain-python-library.svg
    :alt: Supported versions
    :target: https://pypi.org/project/birdbrain-python-library

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/birdbrain-python-library.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/birdbrain-python-library


.. end-badges

Python Library for Birdbrain Technologies Hummingbird Bit and Finch 2

* Free software: GNU Lesser General Public License v3 (LGPLv3)

Installation
============

::

    pip install birdbrain-python-library

You can also install the in-development version with::

    pip install https://github.com/fmorton/BirdBrain-Python-Library/archive/main.zip



Documentation
=============

Finch: https://learn.birdbraintechnologies.com/finch/python/library/

Hummingbird: https://learn.birdbraintechnologies.com/hummingbirdbit/python/library/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox


