#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:App:       loggar
:Purpose:   The ``loggar`` utility is designed to parse Linux log
            files and store the results into a MySQL/MariaDB database
            for auditing.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  Throughout this project, the ``objects.Xlogobject`` objects
            are the primary objects in the project, wrapping the
            log-specific reader objects.

            For example:

                - :class:`objects.loginlogobject.LoginLogFailure`
                - :class:`objects.loginlogobject.LoginLogSuccess`

:Usage:     After activating the target virtual environment and
            installing ``loggar`` ...


            Display the help menu::

                $ loggar --help


            Parse and store successful and failed access (login/logout)
            events::

                $ loggar --access

"""
# pylint: disable=import-error
# pylint: disable=wrong-import-position

import os
import sys
import logging
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
# locals
from libs.argparser import argparser as ap
from libs.database import DatabaseSetup
from libs.enums import ExCode
from objects.accesslogobject import AccessLogSuccess, AccessLogFailure

logger = logging.getLogger(__name__)


class Loggar:
    """Primary application controller class."""

    def __init__(self):
        """Primary application class initialiser."""
        ap.parse()

    def main(self):
        """Primary application process controller."""
        if ap.args.setup:
            self._setup()
        if ap.args.access:
            self._access()

    def _access(self):
        """Process access log entries.

        This method collects and stores both successful and failed login
        attempts.

        """
        logger.info('Collecting and storing *successful* access attempts ...')
        s, count = AccessLogSuccess().run()
        if s:
            logger.info('Completed successfully. %s records added.', count)
        else:
            logger.warning('Failed.')
        logger.info('Collecting and storing *failed* access attempts ...')
        s, count = AccessLogFailure().run()
        if s:
            logger.info('Completed successfully. %s records added.', count)
        else:
            logger.warning('Failed.')

    def _setup(self):
        """Setup the database."""
        logger.info('Setting up the database ...')
        DatabaseSetup().setup()
        logger.info('Done.')
        sys.exit(ExCode.OK.value)


# %% Prevent from running on module import.


# Enable running as either a script (dev/debugging) or as an executable.
if __name__ == '__main__':  # pragma: nocover
    l = Loggar()
    l.main()
else:  # pragma: nocover
    def main():
        """Entry-point exposed for the executable.

        The ``"loggar.loggar:main"`` value is set in
        ``pyproject.toml``'s ``[project.scripts]`` table as the
        entry-point for the installed executable.

        """
        # pylint: disable=redefined-outer-name
        l = Loggar()
        l.main()
