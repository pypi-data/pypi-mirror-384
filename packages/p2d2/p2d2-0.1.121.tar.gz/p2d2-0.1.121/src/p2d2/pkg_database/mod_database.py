import atexit
import signal
import sqlite3
import sys
from abc import ABC
from functools import cached_property
from pathlib import Path

import pandas as pd
from loguru import logger as log
from pandas import DataFrame
from toomanyconfigs import CWD

from .mod_database_models import IDatabase
from .mod_schema import Schema, Table
from .pkg_util import Analytics, migrate_table_schema


class Database(IDatabase):
    def __init__(self, schema: Schema, cwd: Path = Path.cwd(), **kwargs):
        self.schema: Schema = schema
        if not kwargs.get("name"): self.name = self.schema.__name__
        else: self.name = kwargs.get("name")

        from . import AUTOSAVE
        self.cwd = CWD({f"{self.name}":
            {
                f"{self.name}.db": None,
                "changes.pkl": None,
                "message_queue.pkl": None,
                "config.toml": None,
                "backups": {},
                "cron_jobs": {
                    "autosave.py": AUTOSAVE
                }
            }
        })

        self.path = self.cwd.file_structure[0]
        self.table_schemas: dict[str, type[Table]] = self.schema.get_tables()
        self.empty_tables: dict[str, DataFrame] = self.schema.initialize_dataframes()
        self.tables: dict[str, DataFrame] = self.schema.initialize_dataframes()
        self.fetch_all()

        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        sys.excepthook = self._exception_handler

        from .mod_crud import Create, Read, Update, Delete
        self.jobs_list = [Create, Read, Update, Delete]
        _ = self.message_queue
        _ = self.cron

    def _cleanup(self):
        log.debug(f"{self}: Program exiting, committing database")
        self.commit_all()
        self.pkl.commit()

    def _signal_handler(self, signum, frame):
        log.debug(f"{self}: Received signal {signum}, committing database")
        self.commit_all()
        self.pkl.commit()

    def _exception_handler(self, exc_type, exc_value, exc_traceback):
        log.warning(f"{self}: Unhandled exception detected, committing database")
        self.commit_all()
        self.pkl.commit()
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def __repr__(self):
        return f"[{self.name}.db]"

    def get_table(self, table_name: str):
        """Get a table with NaN values properly handled based on type annotations"""
        try:
            table = self.tables[table_name]
        except KeyError:
            raise KeyError(f"Table {table_name} not found in database")

        table_schema = self.table_schemas[table_name]

        for col, expected_type in table_schema.__annotations__.items():
            if col in table.columns:
                if expected_type == bool:
                    table[col] = table[col].fillna(False).astype(bool)
                elif expected_type == int:
                    table[col] = table[col].fillna(0).astype('int64')
                elif expected_type == float:
                    table[col] = table[col].fillna(0.0).astype('float64')
                elif expected_type == str:
                    table[col] = table[col].fillna('').astype('object')

        return table

    def fetch(self, table_name: str = None):
        with sqlite3.connect(self.path) as conn:
            try:
                df_from_sql = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                comparison = Analytics.from_dataframe(df_from_sql).compare_schema(
                    self.empty_tables[table_name], df_from_sql
                )
                log.debug(
                    f"{self}: Got comparison for table '{table_name}' between its schema and current shape: \n - {comparison}")

                if comparison["is_different"]:
                    log.warning(f"{self}: Schema for table '{table_name}' is different from current shape!")
                    migrate_table_schema(self, table_name, self.table_schemas[table_name], comparison)

                self.tables[table_name] = df_from_sql
                log.debug(f"{self}: Read {table_name} from database")
                return True

            except pd.errors.DatabaseError:
                log.warning(f"{self}: Table {table_name} doesn't exist yet. Creating it...")
                self.commit(table_name)
                return False

    def fetch_all(self):
        successes = 0
        for table_name in self.table_schemas.keys():
            if self.fetch(table_name):
                successes += 1

        if successes > 0:
            log.success(f"{self}: Successfully loaded {successes} table(s) from {self.path}")

    def commit(self, table_name: str):
        with sqlite3.connect(self.path) as conn:
            df_copy = self.get_table(table_name).copy()
            for col in df_copy.columns:
                if df_copy[col].dtype == 'datetime64[ns]' or 'datetime' in str(df_copy[col].dtype):
                    df_copy[col] = pd.to_datetime(df_copy[col]).astype('datetime64[ns]').astype(object)

            df_copy.to_sql(table_name, conn, if_exists='replace', index=False)
            log.debug(f"{self}: Wrote {table_name} to database")

    def commit_all(self):
        for table_name, table_df in self.tables.items(): self.commit(table_name)

    @cached_property
    def pkl(self):
        from .pkg_pkl import PickleChangelog
        return PickleChangelog(self)

    @cached_property
    def message_queue(self):
        from .mod_mq import Executor, State
        from .mod_mq import DatabaseMessageQueue
        return DatabaseMessageQueue(self, Executor, State, self.jobs_list)

    def create(self, table_name: str, signature: str, **kwargs):
        message = {"table_name": table_name, "signature": signature} | kwargs
        return self.message_queue.new_message(job_type="create", **message)

    def read(self, table_name: str, **conditions):
        message = {"table_name": table_name} | conditions
        return self.message_queue.new_message(job_type="read", **message)

    def update(self, table_name: str, signature: str, **kwargs):
        message = {"table_name": table_name, "signature": signature} | kwargs
        return self.message_queue.new_message(job_type="update", **message)

    def delete(self, table_name: str, signature: str, **conditions):
        message = {"table_name": table_name, "signature": signature} | conditions
        return self.message_queue.new_message(job_type="delete", **message)

    @cached_property
    def cron(self):
        from .mod_cron import CronManager, CronLoader
        return CronManager(self, CronLoader)