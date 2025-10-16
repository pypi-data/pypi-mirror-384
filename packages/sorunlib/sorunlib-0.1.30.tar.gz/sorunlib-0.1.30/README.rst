========
sorunlib
========

| |pypi| |versions| |license|
| |tests| |pre-commit| |coverage| |docs|

Overview
--------

A high level library for running observatory operations. `sorunlib` handles
connecting to and controlling multiple OCS Agents, sending the appropriate
commands for orchestrating observations for a single telescope platform.

Installation
------------

Install and update using pip::

    $ pip install -U sorunlib

Install optional dependencies with::

    $ pip install -U sorunlib[dev]
    $ pip install -U sorunlib[docs]
    $ pip install -U sorunlib[dev,docs]

Documentation
-------------

The sorunlib documentation can be built using Sphinx. Be sure to install the
optional "docs" dependencies when installing above. Then run::

  $ cd docs/
  $ make html

You can then open ``docs/_build/html/index.html`` in your preferred web
browser. You can also find a copy hosted on `Read the Docs`_.

.. _Read the Docs: https://sorunlib.readthedocs.io/en/latest/

Tests
-----

The tests can be run using pytest, and should be run from the ``tests/``
directory::

    $ cd tests/
    $ python3 -m pytest

Contributing
------------

For guidelines on how to contribute to sorunlib see `CONTRIBUTING.rst`_.

.. _CONTRIBUTING.rst: https://github.com/simonsobs/sorunlib/blob/main/CONTRIBUTING.rst

License
-------

This project is licensed under the BSD 2-Clause License - see the
`LICENSE.txt`_ file for details.

.. _LICENSE.txt: https://github.com/simonsobs/sorunlib/blob/main/LICENSE.txt


.. |coverage| image:: https://codecov.io/github/simonsobs/sorunlib/graph/badge.svg?token=701SYU7A4I
    :target: https://codecov.io/github/simonsobs/sorunlib

.. |docs| image:: https://readthedocs.org/projects/sorunlib/badge/?version=latest
    :target: https://sorunlib.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |license| image:: https://img.shields.io/pypi/l/sorunlib
   :target: LICENSE.txt
   :alt: PyPI - License

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/simonsobs/sorunlib/main.svg
   :target: https://results.pre-commit.ci/latest/github/simonsobs/sorunlib/main
   :alt: pre-commit.ci status

.. |pypi| image:: https://img.shields.io/pypi/v/sorunlib
   :target: https://pypi.org/project/sorunlib/
   :alt: PyPI - Version

.. |tests| image:: https://github.com/simonsobs/sorunlib/actions/workflows/pytest.yml/badge.svg
    :target: https://github.com/simonsobs/sorunlib/actions/workflows/pytest.yml
    :alt: GitHub Actions Workflow Status

.. |versions| image:: https://img.shields.io/pypi/pyversions/sorunlib
   :alt: PyPI - Python Version
