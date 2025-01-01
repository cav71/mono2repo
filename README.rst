=========
mono2repo
=========

.. image:: https://img.shields.io/pypi/v/mono2repo.svg
   :target: https://pypi.org/project/mono2repo
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/mono2repo.svg
   :target: https://pypi.org/project/mono2repo
   :alt: Python versions

.. image:: https://github.com/cav71/mono2repo/actions/workflows/master.yml/badge.svg
   :target: https://github.com/cav71/mono2repo/actions
   :alt: Build

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black

.. image:: https://codecov.io/gh/cav71/mono2repo/branch/master/graph/badge.svg?token=FZB02O3V2G
   :target: https://codecov.io/gh/cav71/mono2repo
   :alt: Coverage


This package (and related script) extracts the content of a subdirectory in a monorepo and 
it creates a stand alone repo (copying the related history).

Let say you have a monorepo with multiple projects (project1, project2 etc.) 
and we wan to make project1 a stand alone repo (retaining the project1 history)::

    monorepo/
    ├── README.TXT
    ├── misc
    │   └── more
    └── subfolder
        ├── project1           # <-- we want to extract this
        │   └── a
        │       ├── hello.txt
        │       └── subtree
        ├── project2
        └── project3

Using mono2repo to extract project1::

    mono2repo init -v project1 monorepo/subfolder/project1

Will generate::

    monorepo/
    ├── README.TXT
    ├── misc
    ...
    project1/
    └── a
        ├── hello.txt
        └── subtree


Installation
------------
You can install ``mono2repo`` via `pip`_ from `PyPI`_::

    $ pip install mono2repo


Example
-------

For this example we first create the summary repo from the main pelican monorepo,
then we update the summary with the new upstream changes::

    https://github.com/getpelican/pelican-plugins.git
    ....
    └ summary/
     ├── Readme.rst
     └── summary.py

Create a new repo
-----------------

First we create a new repo::

    mono2repo init summary-extracted \
        https://github.com/getpelican/pelican-plugins.git/summary

.. NOTE::
    summary-extracted has two branches master and the migrate (leave this alone!).  It is not time to merge the changes into master::

        > cd summary-extracted
        > git checkout master
        > git merge migrate

Update the repo
---------------

Update the summary-extracted with the latest summary related changes::

    mono2repo update summary-extracted

.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
