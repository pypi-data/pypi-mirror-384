#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This reader module provides functionality to parse
            successful login/logout attempts, using a call to the
            ``last`` program.

            The counterpart module :mod:`~lastbreader` parses failed
            login/logout attempts using a call to the ``lastb`` program,
            using functionality inherited from this module.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error
# pylint: disable=wrong-import-order

import logging
import subprocess as sp
# locals
from readers._basereader import _BaseReader

logger = logging.getLogger(__name__)


class LastReader(_BaseReader):
    """Reader class for *successful* login attempts by calling ``last``.

    Args:
        host (str): Hostname.
        ip (str): IP address; used for SSH.
        port (int, optional): SSH port. Defaults to 22.

    """

    # Command written as a string rather than args due to the pipe.
    _CMD = ["last -adwx --time-format iso -s 00:00 | head -n-1"]

    def _read(self):
        """Read the ``last`` (or ``lastb``) log for a specific host.

        In this case, a subprocess call is made to the ``last`` or
        ``lastb`` program and the output is captured and parsed. If the
        host is remote, the command is run via SSH.

        If the log is read successfully, the text is stored into the
        :attr:`_text` class attribute for external access via the
        :attr:`text` property.

        """
        # pylint: disable=attribute-defined-outside-init  # It's in the parent class.
        ssh = []
        shell = True  # Must be True when not using SSH.
        if self._host.lower() not in ('localhost', self._ME) or self._ip != '127.0.0.1':
            ssh = ['ssh', '-t', f'{self._USER}@{self._ip}', '-p', self._port]
            shell = False
        cmd = ssh + self._CMD
        logger.debug('Executing command: %s', ' '.join(cmd))
        with sp.Popen(cmd, stderr=sp.PIPE, stdout=sp.PIPE, shell=shell) as proc:
            stdout, stderr = proc.communicate()
            if stderr and not stdout:
                logging.error('Error occurred while reading log: %s', stderr.decode().strip())
                logging.error('Log text not being stored.')
            else:
                self._text = stdout.decode(encoding='ascii').strip()
                logging.debug('Log data collected successfully.')
                logging.debug('Text:\n%s', self._text if self._text else '[empty log]')


class LastbReader(LastReader):
    """Reader class for *failed* login attempts by calling ``lastb``.

    This class inherits the functionality of the :class:`LastReader`
    class, and modifies the command by replacing ``last`` with ``lastb``
    and elevates permission.

    Args:
        host (str): Hostname.
        ip (str): IP address; used for SSH.
        port (int, optional): SSH port. Defaults to 22.

    """

    # Command written as a string rather than args due to the pipe.
    _CMD = ["sudo lastb -adwx --time-format iso -s 00:00 | head -n-1"]
