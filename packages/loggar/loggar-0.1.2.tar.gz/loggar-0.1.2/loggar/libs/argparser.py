#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the project's command line argument
            parsing functionality.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

import argparse
import logging
import sys
# locals
from libs.config import systemcfg, projectcfg
from libs.enums import ExCode
from libs._version import __version__


class ArgParser:
    """Project command line argument parser."""

    # Program usage and help strings.
    _proj = projectcfg['name']
    _desc = projectcfg['desc']
    _usag = projectcfg['usage']
    _vers = __version__
    _h_acce = 'Collect and store access (login/logout) events.'
    _h_dbug = 'Display debugging output to the terminal.'
    _h_help = 'Display this help and usage, then exit.'
    _h_setu = ('Setup the database by creating the database and any (new) tables,\n'
               'then exit.')
    _h_vers = 'Display the version, then exit.'

    # At least one of these tasks is required.
    _REQD_TASKS = ('access', 'setup')

    def __init__(self):
        """Project argument parser class initialiser."""
        self._args = None
        self._parser = None  # Underlying argument parser.
        self._epil = self._build_epilog()

    @property
    def args(self):
        """Accessor to parsed arguments."""
        return self._args

    def parse(self):
        """Parse command line arguments."""
        # pylint: disable=line-too-long
        argp = argparse.ArgumentParser(prog=self._proj,
                                       usage=self._usag,
                                       description=self._desc,
                                       epilog=self._epil,
                                       formatter_class=argparse.RawTextHelpFormatter,
                                       add_help=False)
        # Order matters here as it affects the display -->
        argp.add_argument('-a', '--access', help=self._h_acce, action='store_true')
        argp.add_argument('-s', '--setup', help=self._h_setu, action='store_true')
        argp.add_argument('-d', '--debug', help=self._h_dbug, action='store_true')
        argp.add_argument('-h', '--help', help=self._h_help, action='help')
        argp.add_argument('-v', '--version', help=self._h_vers, action='version', version=self._epil)
        self._parser = argp
        self._args = argp.parse_args()
        self._set_logger()
        logging.debug('Arguments: %s', self._args)
        self._verify_args()

    def _build_epilog(self) -> str:
        """Build the epilog string for terminal display.

        Returns:
            str: A string containing the text to be displayed in the
            epilog of the help menu.

        """
        epil = f'{self._proj} v{self._vers}'
        return epil

    def _set_logger(self):
        """Set the debugging level based on the CLI argument.

        The default logging level is set using the ``project.log_level``
        key in ``config.toml``. However, if the ``--debug`` argument is
        passed, the log level is set to 10 (DEBUG).

        :Levels:
            - 10: DEBUG
            - 20: INFO
            - 30: WARNING
            - 40: ERROR
            - 50: CRITICAL

        """
        level = 10 if self._args.debug else systemcfg['loglevel']
        logging.basicConfig(level=level, format=systemcfg['logfmt'])

    def _verify_args(self):
        """Verify the required arguments are available.

        :Rules:
            At least one of the :attr:`_REQD_TASKS` must be ``True`` in
            the parsed arguments.

            If this check validates to ``False``, program usage is
            displayed and the appropriate exit code is set.

        """
        if not any(getattr(self._args, i) for i in self._REQD_TASKS):
            self._parser.print_help()
            print()
            logging.error('At least one of the following tasks is required: %s', self._REQD_TASKS)
            print()
            sys.exit(ExCode.ERR_ARGS_REQD.value)


# Make the arg parser accessible as an import.
argparser = ArgParser()
