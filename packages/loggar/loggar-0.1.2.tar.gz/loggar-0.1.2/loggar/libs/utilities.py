#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the utility-based functionality to the 
            project.

:Platform:  Linux/Windows | Python 3.8+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

import logging
import socket

logger = logging.getLogger(__name__)


class Utilities:
    """Class wrapper for utility-based functionality."""

    @staticmethod
    def ping(ipaddr: str, port: int) -> bool:
        """Verify the target host is reachable.

        Args:
            ipaddr (str): IP address for the target host.
            port (int): Port for the target host.

        Returns:
            bool: True if a connection can be established with the target
            host, otherwise False.
        
        """
        try:
            socket.setdefaulttimeout(3)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ipaddr, port))
        except OSError:
            logger.info('Host unreachable: %s', ipaddr)
            return False
        s.close()
        return True


utilities = Utilities()

