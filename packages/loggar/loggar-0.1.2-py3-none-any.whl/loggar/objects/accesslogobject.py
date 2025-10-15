#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module contains the functionality specific to
            collecting, parsing, preparing and storing log data for
            successful and failed access attempts.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

:Example:
            Collect, parse and store logs for *successful* access
            attempts::

                >>> from objects.accesslogobject import AccessLogSuccess

                >>> AccessLogSuccess().run()


            Collect, parse and store logs for *failed* access attempts::

                >>> from objects.accesslogobject import AccessLogFailed

                >>> AccessLogFailed().run()

"""
# pylint: disable=import-error
# pylint: disable=too-few-public-methods  # Supplied by the private base class.
# pylint: disable=wrong-import-order

import logging
import pandas as pd
import re
# locals
from libs.config import systemcfg
from libs.database import seclogsdb
from objects._baselogobject import _BaseLogObject
from readers.lastreader import LastReader, LastbReader

logger = logging.getLogger(__name__)


class _AccessLogBase(_BaseLogObject):
    """Private base class providing functionality for access logs."""

    def __init__(self):
        """Base access log class initialiser."""
        super().__init__()
        self._logtype = 'access'

    def _collect(self) -> bool:
        """Collect the relevant log file for all hosts.

        Returns:
            bool: True, if the number of readers is equal to the number
            of hosts in the config file.

        """
        # pylint: disable=not-callable  # _Reader
        for key in systemcfg['hosts']:
            host, ip, port = key.values()
            logger.debug('-'*75)
            logger.info('Processing %s for: %s', self._logtype, host)
            r = self._Reader(host=host, ip=ip, port=port)
            r.read()
            self._readers.append(r)
        return len(self._readers) == len(systemcfg['hosts'])

    def _parse_and_prep(self) -> bool:
        """Parse and prepare each reader's log into a DataFrame.

        Returns:
            bool: True, if *both* datasets (log text and DataFrame) are
            empty or populated. Otherwise False if one is populated and
            not the other.

        """
        rexp = re.compile(systemcfg['regex'][self._logtype])
        for r in self._readers:
            tmp = []
            logger.debug('Parsing log data for: %s', r.host)
            for entry in r.text.split('\n'):
                m = rexp.match(entry.strip())
                if m:
                    tmp.append(m.groupdict())
            df = pd.DataFrame(tmp)
            r.data = self._prep(df=df, reader=r)
            logger.debug('DataFrame:\n%s', r.data)
        return all(not r.data.empty & bool(r.text) for r in self._readers)

    def _prep(self, df: pd.DataFrame, reader: object):
        """Prepare each reader's DataFrame for storage.

        Args:
            df (pd.DataFrame): A DataFrame containing the log data to be
                prepared for storage.
            reader (object): The reader object which may contain specific
                data to be added to the DataFrame.

        :Processing:
            - Convert the timein and timeout values to datetime objects.
            - Filter the entries to exclude 'reboot', 'runlevel' and
              'shutdown'.
            - Parse the duration values.

        """
        if not df.empty:
            logger.debug('Preparing DataFrame for storage')
            fmt = systemcfg[self._logtype]['datefmt']
            df = df.assign(
                           hostname=reader.host,
                           timein=pd.to_datetime(df['timein'], format=fmt),
                           timeout=pd.to_datetime(df['timeout'], format=fmt, errors='coerce'),
                          )
            df = df[~df['uname'].isin(('reboot', 'runlevel', 'shutdown'))]
            df = df.rename(columns={'dur': 'duration'})
            logger.debug('Done')
        return df

    def _store(self) -> tuple[bool, int]:
        """Store all prepared logs to the database.

        Returns:
            tuple[bool, int]: A tuple containing a boolean success flag
            indicating the success of the data insert and an integer
            indicating the number of records added.

        """
        count = 0
        success = []
        for r in self._readers:
            logger.debug('Storing %s %s log for: %s', self._subtype, self._logtype, r.host)
            flag, n = seclogsdb.to_sql(df=r.data, table_name=self._table_name, unique=True)
            logger.debug('Added %d records', n)
            success.append(flag)
            count += n
        return all(success), count


class AccessLogFailure(_AccessLogBase):
    """Class providing functionality for failed access attempts."""

    def __init__(self):
        """Base failed access log class initialiser."""
        # pylint: disable=invalid-name  # Correct. Reader is a class.
        super().__init__()
        self._Reader = LastbReader
        self._subtype = 'failure'
        self._table_name = 'access_failure'


class AccessLogSuccess(_AccessLogBase):
    """Class providing functionality for successful access attempts."""

    def __init__(self):
        """Base successful access log class initialiser."""
        # pylint: disable=invalid-name  # Correct. Reader is a class.
        super().__init__()
        self._Reader = LastReader
        self._subtype = 'success'
        self._table_name = 'access_success'
