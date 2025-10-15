
# A utility for archiving Linux log files

[![PyPI - Version](https://img.shields.io/pypi/v/loggar?style=flat-square)](https://pypi.org/project/loggar)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/loggar?style=flat-square)](https://pypi.org/project/loggar)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/loggar?style=flat-square)](https://pypi.org/project/loggar)
[![PyPI - Status](https://img.shields.io/pypi/status/loggar?style=flat-square)](https://pypi.org/project/loggar)
[![Static Badge](https://img.shields.io/badge/tests-pending-orange?style=flat-square)](https://pypi.org/project/loggar)
[![Static Badge](https://img.shields.io/badge/code_coverage-pending-orange?style=flat-square)](https://pypi.org/project/loggar)
[![Static Badge](https://img.shields.io/badge/pylint_analysis-100%25-brightgreen?style=flat-square)](https://pypi.org/project/loggar)
[![Documentation Status](https://readthedocs.org/projects/loggar/badge/?version=latest&style=flat-square)](https://loggar.readthedocs.io/en/latest/)
[![PyPI - License](https://img.shields.io/pypi/l/loggar?style=flat-square)](https://opensource.org/licenses/MIT)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/loggar?style=flat-square)](https://pypi.org/project/loggar)

## Overview
The **log** **ar**-chive project (aka ``loggar``) is a Linux command line utility (written in CPython) designed to traverse a network of listed servers and collect, transform and store their log data into a central database.

This approach enables the system administrators to not only archive important log files, but also provides a means by which the logs can be easily retrieved and audited, should the need arise.


### Toolset
The current toolset enables the collection and storage of the following log types:

- Access attempts (successful and failed)

Coming soon:

- Shutdown/reboot cycles
- SSH access attempts (successful and failed)

For descriptive usage for each, please refer to the [Command Line Usage](#Command-Line-Usage) section.


## Installation and Setup

### Installation
The easiest way to install ``loggar`` is using ``pip`` *after* activating the target virtual environment:

    pip install loggar

This will install *both* the library and the command line utility, but we'll just be using the command line utility.

After installation, check the utility was installed and is accessible using:

    loggar --help

Additional (older) releases can be found either at [PyPI](https://pypi.org/project/loggar/#history) or in [GitHub Releases](https://github.com/s3dev/loggar/releases).

### Database setup
First, the MySQL or MariaDB database and tables must be created. The creation scripts are provided for you in the ``meta/database/setup`` directory, if you'd like to run the setup yourself. Alternatively, the following command can be called to setup the database for you:

    loggar --setup

> **Note:** The database engine must already be installed and at least one user created.
            Additionally, the user's credentials must be added to the ``config.toml`` file.

### Config file setup
Once the database is setup, you're ready to update the config file. To do this, simply navigate to the ``loggar/libs/config.toml`` file and populate the database credentials to the ``[database]`` table.

Next, populate the network hosts which should be swept to the ``[system.hosts]`` table. Hosts can be added or removed at any time with no further setup required.

> **Tip:** Both the database setup scripts directory and the ``config.toml`` file can be found within the ``site-packages`` directory for the target virtual environment.


## Command Line Usage

### Help and usage
Call up the help and usage menu at any time using:

    loggar --help

### Collecting and storing: Access attempts
To collect to store user access attempts (failed and successful), use:

    loggar --access 

### Running on a schedule
To collect logs at regular intervals, a ``cron`` task can be setup with the appropriate arguments for the relevant log files.

> **Note:** Remember to include the path to the target virtual environment's Python executable in the cron command.


## Troubleshooting
No troubleshooting guidance at this time.

