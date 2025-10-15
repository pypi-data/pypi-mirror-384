A Python and Command-Line Interface to Archive.org
==================================================

|tox|
|versions|
|downloads|
|contributors|

.. |tox| image:: https://github.com/jjjake/internetarchive/actions/workflows/tox.yml/badge.svg
    :target: https://github.com/jjjake/internetarchive/actions/workflows/tox.yml

.. |versions| image:: https://img.shields.io/pypi/pyversions/internetarchive.svg
    :target: https://pypi.org/project/internetarchive

.. |downloads| image:: https://static.pepy.tech/badge/internetarchive/month
    :target: https://pepy.tech/project/internetarchive

.. |contributors| image:: https://img.shields.io/github/contributors/jjjake/internetarchive.svg
    :target: https://github.com/jjjake/internetarchive/graphs/contributors

This package installs a command-line tool named ``ia`` for using Archive.org from the command-line.
It also installs the ``internetarchive`` Python module for programmatic access to archive.org.
Please report all bugs and issues on `Github <https://github.com/jjjake/internetarchive/issues>`__.

SECURITY NOTICE
_______________

**Please upgrade to v5.4.2+ immediately.** Versions <=5.4.1 contain a critical directory traversal vulnerability in the ``File.download()`` method. `See the changelog for details <https://github.com/jjjake/internetarchive/blob/master/HISTORY.rst>`_. Thank you to Pengo Wray for their contributions in identifying and resolving this issue.

Installation
------------

You can install this module via `pipx <https://pipx.pypa.io/stable/>`_:

.. code:: bash

    $ pipx install internetarchive

Binaries of the command-line tool are also available:

.. code:: bash

    $ curl -LO https://archive.org/download/ia-pex/ia
    $ chmod +x ia
    $ ./ia --help

Unsupported Installation Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**This library must only be installed via** `one of the supported methods <https://archive.org/developers/internetarchive/installation.html>`_ **(i.e.** ``pip``, ``pipx``, **or from source).**

Installation via third-party package managers like Homebrew, MacPorts, or Linux system packages (apt, yum, etc.) is **not supported**. These versions are often severely outdated, incompatible, and broken.

If you have installed this software via Homebrew, please uninstall it (`brew uninstall internetarchive`) and use a supported method.

Documentation
-------------

Documentation is available at `https://archive.org/services/docs/api/internetarchive <https://archive.org/services/docs/api/internetarchive>`_.


Contributing
------------

All contributions are welcome and appreciated. Please see `https://archive.org/services/docs/api/internetarchive/contributing.html <https://archive.org/services/docs/api/internetarchive/contributing.html>`_ for more details.
