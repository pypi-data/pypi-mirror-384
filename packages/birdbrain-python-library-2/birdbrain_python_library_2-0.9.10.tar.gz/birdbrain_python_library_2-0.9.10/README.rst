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
.. |docs| image:: https://readthedocs.org/projects/BirdBrain-Python-Library-2/badge/?style=flat
    :target: https://BirdBrain-Python-Library-2.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/fmorton/BirdBrain-Python-Library-2/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/fmorton/BirdBrain-Python-Library-2/actions

.. |requires| image:: https://requires.io/github/fmorton/BirdBrain-Python-Library-2/requirements.svg?branch=main
    :alt: Requirements Status
    :target: https://requires.io/github/fmorton/BirdBrain-Python-Library-2/requirements/?branch=main

.. |codecov| image:: https://codecov.io/gh/fmorton/BirdBrain-Python-Library-2/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://codecov.io/github/fmorton/BirdBrain-Python-Library-2

.. |version| image:: https://img.shields.io/pypi/v/birdbrain-python-library-2.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/birdbrain-python-library-2

.. |wheel| image:: https://img.shields.io/pypi/wheel/birdbrain-python-library-2.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/birdbrain-python-library-2

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/birdbrain-python-library-2.svg
    :alt: Supported versions
    :target: https://pypi.org/project/birdbrain-python-library-2

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/birdbrain-python-library-2.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/birdbrain-python-library-2


.. end-badges

Rewritten Python Library for Birdbrain Technologies Hummingbird Bit and Finch 2

Rewrite inspired by https://github.com/BirdBrainTechnologies/BirdBrain-Python-Library

* Free software: GNU Lesser General Public License v3 (LGPLv3)

Installation
============

::

    pip install birdbrain-python-library-2

You can also install the in-development version with::

    pip install https://github.com/fmorton/BirdBrain-Python-Library-2/archive/main.zip



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


