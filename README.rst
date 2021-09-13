=========
mono2repo
=========

This module (and related script) extracts the content of a subtree in a monorepo and it creates a stand alone repo (copying the related history).

Let say you have a monorepo with multiple projects (project1, project2 etc.) 
and we wan to make project1 a stand alone repo (retaining the project1 hostory)::

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

The command to to this is::

    mono2repo init -v project1 monorepo/subfolder/project1

Installation
------------
You can install ``mono2repo`` via `pip`_ from `PyPI`_::

    $ pip install mono2repo

The mono2repo.py is a standalone script and it can be just dowloaded::

    curl -LO https://raw.githubusercontent.com/cav71/mono2repo/master/mono2repo.py


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
