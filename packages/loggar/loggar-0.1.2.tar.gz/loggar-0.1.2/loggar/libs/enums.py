#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the various enumerators to the project.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

import enum


class ExCode(enum.IntEnum):
    """Exit code enumerator class."""

    # Main (1-10)
    OK = 0                  # All OK
    ERR_MAIN = 1            # Error from the LogP.main, the main error handler.

    # Config module (21-29)
    ERR_TOML_INST = 21      # The toml module is not installed (< 3.11).

    # Argument parser (31-39)
    ERR_ARGS_REQD = 31
