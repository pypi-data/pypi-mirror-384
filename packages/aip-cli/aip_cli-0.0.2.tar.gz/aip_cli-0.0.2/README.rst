aip-cli
========

This package provides a unified command line interface to Renesas AI
platform Service.

Jump to: - `Getting Start <#installation>`__

Requirements
~~~~~~~~~~~~

The aws-cli package works on Python versions:

-  3.9.x and greater
-  3.10.x and greater
-  3.11.x and greater
-  3.12.x and greater

Installation
------------

For Developers
^^^^^^^^^^^^^^

aip-cli’s dependencies use a range of packaging features provided by
``wheel`` and ``setuptools``. To ensure smooth installation, it’s
recommended to use:

Create virtual env

::

   cd aip-cli
   python3 -m venv .venv

Install Pre-requisites

::

   .venv/bin/pip3 install build wheel

Building wheel package

::

   .venv/bin/python3 -m build --wheel

Install package

::

   .venv/bin/pip3 install --force-reinstall dist/aip-<version>-py3-none-any.whl # add --force-reinstall so as to force re-write the package

For end users
^^^^^^^^^^^^^

End users only need to install the packged aip-cli with pip command.

::

   pip3 install <public aip package name>
