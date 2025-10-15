=================================
Log Archive Project Documentation
=================================

.. contents:: Page Contents
    :local:
    :depth: 1


Overview
========
The **log** **ar**-chive project (aka ``loggar``) is a Linux command line
utility, written in CPython, designed to traverse a network of listed 
servers and collect, transform and store their log data into a central 
database.

This approach enables the system administrators to not only archive 
important log files, but also provides a means by which the logs
can be easily retrieved and audited, should the need arise.


Toolset
-------
The current toolset enables the collection and storage of the following
log types:

- Access attempts (successful and failed)

Coming soon:

- Shutdown/reboot cycles
- SSH access attempts (successful and failed)

For descriptive usage for each, please refer to the 
:ref:`command-line-usage` section.


Installation and Setup
======================

Installation
------------

The easiest way to install ``loggar`` is using ``pip`` *after* activating
the target virtual environment::
    
    pip install loggar

This will install *both* the library and the command line utility, but
we'll just be using the command line utility.

After installation, check the utility was installed and is accessible
using::

    loggar --help

Additional (older) releases can be found either at `PyPI`_ or in 
`GitHub Releases`_.

Database setup
--------------
First, the MySQL or MariaDB database and tables must be created. The
creation scripts are provided for you in the ``meta/database/setup`` 
directory, if you'd like to run the setup yourself. Alternatively, the 
following command can be called to setup the database for you::

    loggar --setup

.. important:: 

    The database engine must already be installed and at least one user
    created.

    Additionally, the user's credentials must be added to the 
    ``config.toml`` file - refer to the :ref:`config-file-setup` section.
            

.. _config-file-setup:

Config file setup
-----------------
Once the database is setup, you're ready to update the config file. To
do this, simply navigate to the ``loggar/libs/config.toml`` file and
populate the database credentials to the ``[database]`` table.

Next, populate the network hosts which should be swept to the 
``[system.hosts]`` table. Hosts can be added or removed at any time with 
no further setup required.

.. tip::

    Both the database setup scripts directory and the ``config.toml`` file 
    can be found within the ``site-packages`` directory for the target
    virtual environment.


.. _command-line-usage:

Command Line Usage
==================

Help and usage
--------------
Call up the help and usage menu at any time using::

    loggar --help

Collecting and storing: **Access attempts**
-------------------------------------------
To collect to store user access attempts (failed and successful), use::

    loggar --access 

Running on a schedule
---------------------
To collect logs at regular intervals, a ``cron`` task can be setup with
the appropriate arguments for the relevant log files.

.. tip:: 

    Remember to include the path to the target virtual environment's
    Python executable in the cron command.


Troubleshooting
===============
No troubleshooting guidance at this time.

If you have any questions that are not covered by this documentation, or
if you spot any bugs, issues or have any recommendations, please feel free
to :ref:`contact us <contact-us>`.


Documentation Contents
======================
.. toctree::
    :maxdepth: 1

    changelog
    contact


Indices and Tables
==================
* :ref:`genindex`
* :ref:`modindex`


.. rubric:: Footnotes

.. _GitHub Releases: https://github.com/s3dev/loggar/releases
.. _GitHub: https://github.com/s3dev/loggar
.. _PyPI: https://pypi.org/project/loggar/#history


|lastupdated|

