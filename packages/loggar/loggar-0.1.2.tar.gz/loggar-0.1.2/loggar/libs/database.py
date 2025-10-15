#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the database interface for the project.

:Platform:  Linux/Windows | Python 3.8+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error
# pylint: disable=no-member  # Yes they do.
# pylint: disable=wrong-import-order

import os
import logging
import pandas as pd
import subprocess as sp
from dbilib.database import DBInterface
from glob import glob
from importlib.resources import files
# locals
from libs.config import dbcfg

logger = logging.getLogger(__name__)


class SecurityLogsDB:
    """Wrapper class for interacting with the ``security_logs`` table."""

    _CONNSTR = 'mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{database}'

    def __init__(self):
        """Security logs database interface class initialiser."""
        #
        # Pseudo-inherit the DBInterface class by 'copying'
        # the attributes into this subclass.
        #
        self._dbi = DBInterface(connstr=self._create_connstr())
        fns = [fn for fn in dir(self._dbi) if not fn.startswith('__')]
        for fn in fns:
            setattr(self, fn, self._dbi.__getattribute__(fn))

    def to_sql(self, df: pd.DataFrame, table_name: str, unique: bool=False) -> tuple[bool, int]:
        """Load a DataFrame into SQL.

        Args:
            df (pd.DataFrame): The DataFrame to be loaded.
            table_name (str): Database table name.
            unique (bool, optional): Pass True if unique keys are used on
                the table, and the DataFrame should be loaded row-by-row,
                *ignoring* any duplicate keys. Defaults to False.

        Returns:
            tuple[bool, int]: A tuple containing a boolean success flag
            for the data insertion, and an integer showing the number of
            records inserted; excluding duplicates.

        """
        if not unique:
            return self._to_sql_bulk(df=df, table_name=table_name)
        return self._to_sql_single(df=df, table_name=table_name)

    def _count(self, table_name: str) -> int:
        """Return a count of the rows currently in the table.

        Args:
            table_name (str): Database table name.

        Returns:
            int: Number of records in the given table.

        """
        # Protected from SQL injection by the underlying library.
        return self.execute_query(f'select count(*) from {table_name}', raw=True)[0][0]

    def _create_connstr(self) -> str:
        """Create the conn-string for the ``security_logs`` database.

        Returns:
            str: Connection string for this database.

        """
        return self._CONNSTR.format(**dbcfg)

    def _insert(self, data: pd.DataFrame, table_name: str) -> None:
        """Insert a DataFrame into SQL.

        This method is a very simple wrapper around the :func:`df.to_sql`
        method.

        Args:
            data (pd.DataFrame): DataFrame to be inserted.
            table_name (str): Database table name.

        """
        data.to_sql(name=table_name, con=self.engine, if_exists='append', index=False)

    def _to_sql_bulk(self, df: pd.DataFrame, table_name: str) -> tuple[bool, int]:
        """Load an *entire* DataFrame into SQL.

        This method is useful if the table does not have unique
        constraints. If the table has unique constraints, use the
        :meth:`_to_sql_single` method instead.

        Args:
            df (pd.DataFrame): The DataFrame to be loaded.
            table_name (str): Database table name.

        Returns:
            tuple[bool, int]: A tuple containing a boolean success flag
            for the data insertion, and an integer showing the number of
            records inserted; excluding duplicates.

        """
        try:
            c1 = self._count(table_name=table_name)
            self._insert(data=df, table_name=table_name)
            c2 = self._count(table_name=table_name)
            return True, c2 - c1
        except Exception as err:
            logger.error(err)
            return False, 0

    def _to_sql_single(self, df: pd.DataFrame, table_name: str) -> tuple[bool, int]:
        """Load a DataFrame into SQL, one row at a time.

        This method is useful if the table has unique constraints.
        If the table does not have unique constraints, use the
        :meth:`_to_sql_bulk` method instead.

        Args:
            df (pd.DataFrame): The DataFrame to be loaded.
            table_name (str): Database table name.

        :Comments:
            To address the error:

                - "Failed processing pyformat-parameters; Python
                  'timestamp' cannot be converted to a MySQL type"

            ... the names for all ``datetime64[ns]`` | ``pd.Timestamp``
            fields are collected. Once the row has been converted back
            to a DataFrame, each of these fields are converted using
            :func:`pd.to_datetime`.

        .. important::

            This method *ignores* any duplicated entries. They are
            reported the the terminal via the debug logger, however no
            further action is taken. Any duplicates are not included in
            the returned load count.

        Returns:
            tuple[bool, int]: A tuple containing a boolean success flag
            for the data insertion, and an integer showing the number of
            records inserted; excluding duplicates.

        """
        c = 0
        for _, row in df.iterrows():
            # Get a list of datetime columns to be converted.
            dcols = df.select_dtypes(exclude=[pd.Timestamp]).columns
            try:
                row = row.to_frame().T
                # Address the "Failed processing pyformat-parameters; Python 'timestamp'
                # cannot be converted to a MySQL type" error.
                for col in dcols:
                    row[col] = pd.to_datetime(row[col])
                self._insert(data=row, table_name=table_name)
                c += 1
            except Exception as err:
                if '1062' in repr(err):
                    logger.debug('Skipping: %s', err.orig.msg)
                else:
                    logger.error(err)
                    return False, c
        return True, c


class DatabaseSetup:
    """Setup the database for new and old installations.

    .. note::

        Running the setup multiple times will not harm anything as it is
        *not* destructive. All scripts contain an ``IF NOT EXISTS``
        statement.

        If a new table has been added for a given release, then
        ``--setup`` should be called to create the new table.


    .. important::

        The database engine (either MySQL or MariaDB) must already be
        installed with at least one user created. The user's credentials
        must be set on the ``config.toml`` file.


    :Tasks:
        This setup class is responsible for calling the scripts which:

            - Create the database
            - Create all tables, views and stored procedures

        The scripts which are called can be found in the local
        ``meta/database/setup`` directory.

    """

    # These are strings (rather than args) due to the redirect.
    _CMDD = 'mysql -u{user} -p{pwd} -h{host} < {path}'               # Database
    _CMDO = 'mysql -u{user} -p{pwd} -h{host} -D{database} < {path}'  # Other

    def __init__(self):
        """Database setup class initialiser."""

    def setup(self) -> None:
        """Run all applicable scripts to setup the database."""
        self._create_db()
        self._create_tables()

    def _call(self, cmd: str) -> None:
        """Call the ``mysql`` executable with the given command.

        Args:
            cmd (str): Command string to be called by ``subprocess.Popen``.

        Note:
            If the ``stderr`` stream returns a message, this is displayed
            to the terminal. However, all ``stdout`` output is allowed
            to flow through 'naturally'.

        """
        with sp.Popen(cmd, stderr=sp.PIPE, shell=True) as proc:
            _, stderr = proc.communicate()
        if stderr:
            logging.error('The following command threw this error:\n'
                          'CMD: %s\n'
                          'ERROR:%s\n',
                          cmd,
                          stderr.decode())

    def _create_db(self) -> None:
        """Create the database."""
        logger.info('Creating the database ...')
        path = files('meta.database.setup').joinpath('create_db.sql').as_posix()
        cmd = self._CMDD.format(**dbcfg, path=path)
        self._call(cmd=cmd)

    def _create_tables(self) -> None:
        """Create the database tables."""
        paths = glob(files('meta.database.setup').joinpath('create_table__*.sql').as_posix())
        for path in paths:
            logger.info('Creating table: %s ...', os.path.splitext(path)[0].split('__')[1])
            cmd = self._CMDO.format(**dbcfg, path=path)
            self._call(cmd=cmd)


seclogsdb = SecurityLogsDB()
