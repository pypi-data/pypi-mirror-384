#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module contains the provate base functionality which is
            designed to be inherited and specialised by each log-specific
            object.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  This module is not designed to be interacted with directly,
            only through inheritance.

"""

from __future__ import annotations

import logging
# locals
from libs.database import seclogsdb

logger = logging.getLogger(__name__)


class _BaseLogObject:
    """Private base class providing functionality for all log objects."""

    def __init__(self):
        """Base log object class initialiser."""
        self._readers = []          # Collection of reader objects containing log data.
        self._Reader = None         # Overridden by the specialising class.
        self._logtype = None        # Overridden by the specialising class.
        self._table_name = None     # Overridden by the specialising class.

    @property
    def readers(self) -> list:
        """Public accessor to the readers for parsed logs."""
        return self._readers

    def run(self) -> tuple[bool, int]:
        """Entry-point and callable for log parsing.

        :Processing:
            - Verify the target database table exists.
            - Collect the relevant log from each host.
            - Parse the log text for each reader and prepare for storage.
            - Store the log data to the database.

        This method operates on 'running boolean' logic, whereby the
        calling of each processing step is strictly reliant on the
        successful completion of the previous step. If any step fails
        along the way, the method falls through to the end.

        Returns:
            tuple[bool, int]: A tuple containing a boolean success flag
            (True if all processing completes successfully, otherwise
             False) and the number of records inserted into the database.

        """
        # pylint: disable=multiple-statements
        count = 0
        s = self._table_exists()
        if s: s = self._collect()
        if s: s = self._parse_and_prep()
        if s: s, count = self._store()
        return s, count

    def _collect(self) -> bool:
        """Collect the relevant log file for all hosts.

        This is a stub method to be overridden by the specialising class.

        Returns:
            bool: True, if the log text is populated for all readers.
            Otherwise, False.

        """
        return False

    def _parse_and_prep(self) -> bool:
        """Parse and prepare each reader's log into a DataFrame.

        This is a stub method to be overridden by the specialising class.

        Returns:
            bool: True, if the log data is populated for all readers.
            Otherwise, False.

        """
        return False

    def _prep(self, df: pd.DataFrame):  # noqa  # pylint: disable=undefined-variable
        """Prepare each reader's DataFrame for storage.

        This is a stub method to be overridden by the specialising class.

        Args:
            df (pd.DataFrame): A DataFrame containing the log data to be
                prepared for storage.

        """
        # pylint: disable=unused-argument
        return False

    def _store(self) -> tuple[bool, int]:
        """Store all prepared logs to the database.

        This is a stub method to be overridden by the specialising class.

        """
        return False, 0

    def _table_exists(self) -> bool:
        """Verify the database table exists before proceeding.

        Returns:
            bool: True if the table exists, otherwise False.

        """
        if not seclogsdb.table_exists(table_name=self._table_name):
            logger.critical('Database table does not exist: %s', self._table_name)
            return False
        return True
