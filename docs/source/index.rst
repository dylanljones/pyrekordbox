.. pyrekordbox documentation master file, created by
   sphinx-quickstart on Thu Apr  7 15:06:50 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===========
pyrekordbox
===========

|ci-tests| |pypi-version| |pypi-python-version| |pypi-platform| |pypi-license|

.. |ci-tests| image:: https://img.shields.io/github/workflow/status/dylanljones/pyrekordbox/Test/master?label=test&logo=github&style=flat
   :alt: CI: Tests
   :target: https://github.com/dylanljones/pyrekordbox/actions/workflows/tests.yml
.. |pypi-python-version| image:: https://img.shields.io/pypi/pyversions/pyrekordbox?logo=python&style=flat-square
   :alt: PyPI: Python Version
   :target: https://pypi.org/project/pyrekordbox/
.. |pypi-version| image:: https://img.shields.io/pypi/v/pyrekordbox?logo=pypi&style=flat-square
   :alt: PyPI: Version
   :target: https://pypi.org/project/pyrekordbox/
.. |pypi-platform| image:: https://img.shields.io/badge/platform-win%20%7C%20osx-blue?style=flat
   :alt: PyPI: Platform
   :target: https://pypi.org/project/pyrekordbox/
.. |pypi-license| image:: https://img.shields.io/pypi/l/pyrekordbox?style=flat-square&color=lightgrey
   :alt: PyPI: License
   :target: https://github.com/dylanljones/pyrekordbox/blob/master/LICENSE
.. |style-black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square
   :alt: Code style: black
   :target: https://github.com/psf/black

Pyrekordbox is a Python package for interacting with the library and export data of
Pioneer's Rekordbox DJ Software. It currently supports

- Rekordbox XML database
- Analysis files (ANLZ)
- My-settings files
- Rekordbox 6 `master.db` database

.. admonition:: Disclamer

   This project is not affiliated with Pioneer Corp. or its related companies
   in any way or form and has been written independently! Pyrekordbox is licensed
   under the `MIT license <https://github.com/dylanljones/pyrekordbox/blob/master/LICENSE>`_.


.. warning::
   This project is still under heavy development and might contain bugs or
   have breaking API changes in the future.


Contents
========

.. toctree::
   :maxdepth: 3
   :caption: User Guide

   quickstart
   installation
   tutorial/index


.. toctree::
   :maxdepth: 2
   :caption: File formats

   formats/xml
   formats/anlz
   formats/mysetting
   formats/db6


.. toctree::
   :maxdepth: 2
   :caption: Development

   development/contributing
   development/changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
