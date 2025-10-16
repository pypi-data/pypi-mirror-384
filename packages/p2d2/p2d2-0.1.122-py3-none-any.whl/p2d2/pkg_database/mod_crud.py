import asyncio
import json
import time
from datetime import datetime
from starlette.requests import Request
from . import ICreate, IRead, IUpdate, IDelete
from . import Database
from loguru import logger as log
import pandas as pd


class RequestToCRUD:
    @staticmethod
    def get_table_name(request: Request) -> str:
        return request.query_params.get('table_name')

    @staticmethod
    def get_signature(request: Request) -> str:
        return request.query_params.get('signature', 'unknown')

    @staticmethod
    def get_data(request: Request) -> dict:
        return asyncio.run(request.json())

    @classmethod
    def to_create(cls, request: Request) -> dict:
        return {
            'table_name': cls.get_table_name(request),
            'signature': cls.get_signature(request),
            **cls.get_data(request)
        }

    @classmethod
    def to_read(cls, request: Request) -> dict:
        return {
            'table_name': cls.get_table_name(request),
            **cls.get_data(request)
        }

    @classmethod
    def to_update(cls, request: Request) -> dict:
        data = cls.get_data(request)
        return {
            'table_name': cls.get_table_name(request),
            'signature': cls.get_signature(request),
            'conditions': data.get('conditions', {}),
            'updates': data.get('updates', {})
        }

    @classmethod
    def to_delete(cls, request: Request) -> dict:
        return {
            'table_name': cls.get_table_name(request),
            'signature': cls.get_signature(request),
            **cls.get_data(request)
        }

class Create(ICreate):
    def __init__(self, database: Database, table_name: str, signature: str, **kwargs):
        self.database: Database = database
        self.table_name = table_name
        self.signature = signature
        self.kwargs = kwargs

    def execute(self):
        start_time = time.time()

        try:
            table = self.database.get_table(self.table_name)
            unique_keys = self.database.table_schemas[self.table_name].get_unique_keys()
            log.debug(f"Attempting to create in table '{self.table_name}':\n  - unique_keys: {unique_keys}\n  - kwargs: {self.kwargs}")

        except Exception as e:
            raise KeyError(f"Error retrieving table or unique keys: {e}")

        try:
            if len(unique_keys) > 0 and not table.empty:
                for key in unique_keys:
                    if key in self.kwargs and key in table.columns:
                        existing = table.loc[table[key] == self.kwargs[key]]
                        if not existing.empty:
                            log.debug(f"Found existing record with {key}={self.kwargs[key]}, updating instead")
                            return Update.execute_now(
                                self.database,
                                self.table_name,
                                self.signature,
                                conditions={key: self.kwargs[key]},
                                **self.kwargs
                            )
        except Exception as e:
            raise RuntimeError(f"Error cross-checking unique keys: {e}")

        try:
            new_idx = len(table)
            log.debug(f"Adding new row at index: {new_idx}")

            # Set audit columns
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            table.loc[new_idx, 'created_at'] = now_str #TODO: this needs to be delegated
            table.loc[new_idx, 'created_by'] = self.signature
            table.loc[new_idx, 'modified_at'] = now_str
            table.loc[new_idx, 'modified_by'] = self.signature

            for col, value in self.kwargs.items():
                log.debug(f"Setting {col} = {value} (type: {type(value)})")

                # Serialize complex objects
                if isinstance(value, (dict, list)):
                    import json
                    value = json.dumps(value)
                    log.debug(f"Serialized {col} to JSON string")

                table.loc[new_idx, col] = value

            self.database.pkl.log_change(self.signature, self.table_name, "create")
            elapsed = time.time() - start_time
            log.debug(f"Created row in {self.table_name}: {self.kwargs} (took {elapsed:.4f}s)")
            return table

        except Exception as e:
            import traceback
            log.error(f"Exception in create method: {e}")
            log.error(f"Full traceback: {traceback.format_exc()}")
            raise

    @classmethod
    def execute_now(cls, database: Database, table_name: str, signature, **kwargs):
        inst = cls(database, table_name, signature, **kwargs)
        return inst.execute()

    @classmethod
    def from_request(cls, database: Database, request: Request):
        params = RequestToCRUD.to_create(request)
        return cls(database, **params)

    @classmethod
    def execute_now_from_request(cls, database: Database, request: Request):
        return cls.from_request(database, request).execute()

class Read(IRead):
    def __init__(self, database: Database, table_name: str, **conditions):
        self.database = database
        self.table_name = table_name
        self.conditions = conditions

    def execute(self):
        start_time = time.time()
        table = self.database.get_table(self.table_name)

        if not self.conditions:
            log.debug(f"Read all {len(table)} rows from {self.table_name} (took {time.time() - start_time:.4f}s)")
            return table

        mask = pd.Series([True] * len(table))
        for col, value in self.conditions.items():
            if col in table.columns:
                mask &= (table[col] == value)

        result = table[mask]
        log.debug(f"Read {len(result)} rows from {self.table_name} (took {time.time() - start_time:.4f}s)")
        return result

    @classmethod
    def execute_now(cls, database: Database, table_name: str, **conditions):
        return cls(database, table_name, **conditions).execute()

    @classmethod
    def from_request(cls, database: Database, request: Request):
        params = RequestToCRUD.to_read(request)
        return cls(database, **params)

    @classmethod
    def execute_now_from_request(cls, database: Database, request: Request):
        return cls.from_request(database, request).execute()


class Update(IUpdate):
    def __init__(self, database: Database, table_name: str, signature: str, conditions: dict = None, **kwargs):
        self.database = database
        self.table_name = table_name
        self.signature = signature
        self.conditions = conditions or {}
        self.kwargs = kwargs

    def execute(self):
        start_time = time.time()
        table = self.database.get_table(self.table_name)

        mask = pd.Series([True] * len(table))
        for col, value in self.conditions.items():
            if col in table.columns:
                mask &= (table[col] == value)

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        table.loc[mask, 'modified_at'] = now_str
        table.loc[mask, 'modified_by'] = self.signature

        for col, value in self.kwargs.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if col in table.columns:
                table.loc[mask, col] = value

        updated_count = mask.sum()
        self.database.pkl.log_change(self.signature, self.table_name, "update")
        log.debug(f"Updated {updated_count} rows in {self.table_name} by {self.signature} (took {time.time() - start_time:.4f}s)")
        return table

    @classmethod
    def execute_now(cls, database: Database, table_name: str, signature: str, conditions: dict, **kwargs):
        return cls(database, table_name, signature, conditions, **kwargs).execute()

    @classmethod
    def from_request(cls, database: Database, request: Request):
        params = RequestToCRUD.to_update(request)
        return cls(database, **params)

    @classmethod
    def execute_now_from_request(cls, database: Database, request: Request):
        return cls.from_request(database, request).execute()


class Delete(IDelete):
    def __init__(self, database: Database, table_name: str, signature: str, **conditions):
        self.database = database
        self.table_name = table_name
        self.signature = signature
        self.conditions = conditions

    def execute(self):
        start_time = time.time()
        table = self.database.get_table(self.table_name)

        mask = pd.Series([True] * len(table))
        for col, value in self.conditions.items():
            if col in table.columns:
                mask &= (table[col] == value)

        result = table[~mask].reset_index(drop=True)
        self.database.tables[self.table_name] = result
        deleted_count = len(table) - len(result)
        self.database.pkl.log_change(self.signature, self.table_name, "delete")
        log.debug(f"Deleted {deleted_count} rows from {self.table_name} by {self.signature} (took {time.time() - start_time:.4f}s)")
        return result

    @classmethod
    def execute_now(cls, database: Database, table_name: str, signature: str, **conditions):
        return cls(database, table_name, signature, **conditions).execute()

    @classmethod
    def from_request(cls, database: Database, request: Request):
        params = RequestToCRUD.to_delete(request)
        return cls(database, **params)

    @classmethod
    def execute_now_from_request(cls, database: Database, request: Request):
        return cls.from_request(database, request).execute()