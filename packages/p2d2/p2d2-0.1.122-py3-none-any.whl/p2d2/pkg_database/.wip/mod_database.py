import signal
import sqlite3
import sys
import time
from datetime import date
from functools import cached_property
from pathlib import Path

import pandas as pd
from loguru import logger as log
from toomanyconfigs import CWD


class DatabaseInit:
    _cwd: CWD
    _name: str
    _path: Path
    _backups: Path
    _default_columns: dict[str, type]
    _unique_keys: dict
    _schemas: dict

    def __init__(self, **kwargs):
        # noinspection PyUnboundLocalVariable
        self._name = name if isinstance((name := kwargs.get("db_name") or kwargs.get("name")), str) else self.__class__.__name__
        self._cwd = CWD({f"{self._name}":
            {
                f"{self._name}.db": None,
                "changes.pkl": None,
                "config.toml": None,
                "backups": {}
            }
        })
        self._path = self._cwd.file_structure[0]
        self._backups = self._cwd.cwd / self._name / "backups"
        self._default_columns = {"created_at": str, "created_by": str, "modified_at": str, "modified_by": str}  # TODO: Add default column support in schema class declaration
        self._unique_keys = {}
        self._schemas = {}

class DatabaseBackend(DatabaseInit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from .pkg_util import empty_dataframe_from_type
        for item in self.__annotations__.items():
            a, t = item  # annotation, type
            if a.startswith("_"): continue
            if hasattr(self, a): continue
            df, unique_keys = empty_dataframe_from_type(t, self._default_columns)
            setattr(self, a, df)
            self._schemas[a] = getattr(self, a)
            self._unique_keys[a] = unique_keys

        self._fetch()

        from src.p2d2.pkg_database.pkg_util.mod_analytics import Analytics
        from .pkg_util import migrate_table_schema #TODO mod_types is kind of a misnomer
        for item in self.__annotations__.items():
            a, t = item  # annotation, type
            df_current = self._get_table(a)
            df_schema = self._schemas[a]
            comparison = Analytics.compare_schema(df_schema, df_current)
            log.debug(f"{self}: Got comparison for table '{a}' between its schema and current shape: "
                      f"\n - {comparison}")
            if comparison["is_different"]:
                log.warning(f"{self}: Schema for table '{a}' is different from current shape!")
                migrate_table_schema(self, a, t, comparison)

            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            sys.excepthook = self._exception_handler

    def _signal_handler(self, signum, frame):
        log.debug(f"{self}: Received signal {signum}, committing database")
        self._commit()
        self._pkl.commit()
        exit(0)

    def _exception_handler(self, exc_type, exc_value, exc_traceback):
        log.warning(f"{self}: Unhandled exception detected, committing database")
        self._commit()
        self._pkl.commit()
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def __repr__(self):
        return f"[{self._name}.db]"

    @cached_property
    def _pkl(self):
        from .pkg_pkl import PickleChangelog
        return PickleChangelog(self)

    @property
    def _analytics(self):
        from .pkg_util import Analytics
        analytics = {}
        for name, df in self._tables.items():
            analytics[name] = Analytics.from_dataframe(df)
        return analytics

    @property
    def _tables(self):
        from .pkg_util import TableIndex
        index = TableIndex()  # table index is a subclass of dict with a list attribute
        for attr_name, attr_type in self.__annotations__.items():
            if attr_name.startswith("_"): continue
            index[attr_name] = getattr(self, attr_name, None)
            if index[attr_name] is None: raise KeyError
        if index == {}: raise RuntimeError("Cannot initialize a database with no tables!")
        for item in index.keys():
            index.list.append(getattr(self, item))
        return index

    def _get_table(self, table_name: str):
        """Get a table with NaN values properly handled based on type annotations"""
        table = getattr(self, table_name)
        table_class_name = table_name.capitalize()
        for attr_name, attr_type in self.__annotations__.items():
            if attr_name == table_name:
                type_annotations = attr_type.__annotations__
                break
        else:
            raise Exception(f"Unable to find type annotations for {table_class_name}")

        for col, expected_type in type_annotations.items():
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

    def _backup(self):
        today = date.today()
        folder = self._backups / str(today)

        if not any(self._backups.glob(f"{today}*")):
            log.warning(f"{self}: Backup not found for today! Creating...")
            folder.mkdir(exist_ok=True)
            if folder.exists():
                log.success(f"{self}: Successfully created backup folder at {folder}")
            else:
                raise FileNotFoundError

            for table_name, table_df in self._tables.items():
                backup_path = folder / f"{table_name}.parquet"
                table_df.to_parquet(backup_path)

    def _fetch(self):
        with sqlite3.connect(self._path) as conn:
            successes = 0
            for table_name in self._tables.keys():
                try:
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                    setattr(self, table_name, df)
                    successes = successes + 1
                    log.debug(f"{self}: Read {table_name} from database")
                except pd.errors.DatabaseError:
                    log.debug(f"{self}: Table {table_name} doesn't exist, keeping empty DataFrame")

            if successes == 0:
                log.warning(f"{self}: No _tables were successfully registered. "
                            f"This probably means the database is empty. Attempting to write...")
                self._commit()
            else:
                log.success(f"{self}: Successfully loaded {successes} _tables from {self._path}")

    def _commit(self):
        self._backup()
        with sqlite3.connect(self._path) as conn:
            for table_name, table_df in self._tables.items():
                df_copy = table_df.copy()
                for col in df_copy.columns:
                    if df_copy[col].dtype == 'datetime64[ns]' or 'datetime' in str(df_copy[col].dtype):
                        df_copy[col] = pd.to_datetime(df_copy[col]).astype('datetime64[ns]').astype(object)

                df_copy.to_sql(table_name, conn, if_exists='replace', index=False)
                log.debug(f"{self}: Wrote {table_name} to database")

class Database():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)