from typing import Type

import pandas as pd
from loguru import logger as log

from ..mod_schema import python_to_dtype


def migrate_table_schema(self, table_name: str, table_type: Type, comparison: dict):
    # from .. import Database
    # self: Database
    # if not isinstance(self, Database): raise TypeError(f"This method must be called on a Database instance, got {type(self)} instead") #TODO: Reenable
    log.info(f"{self}: Starting schema migration for table '{table_name}'")

    if comparison["only_in_df1"]:
        log.info(f"{self}: Adding {len(comparison['only_in_df1'])} new columns to '{table_name}' DataFrame")

        table_df = self.tables[table_name]
        type_annotations = self.table_schemas[table_name].__annotations__

        for col in comparison["only_in_df1"]:
            if col in type_annotations:
                python_type = type_annotations[col]
                dtype = python_to_dtype(python_type)
                table_df[col] = pd.Series(dtype=dtype)
                log.success(f"{self}: Added column '{col}' ({dtype}) to DataFrame '{table_name}'")
            else:
                table_df[col] = pd.Series(dtype='object')
                log.warning(f"{self}: Column '{col}' not found in type annotations, defaulting to 'object'")

        self.tables[table_name] = table_df

    if comparison["only_in_df2"]:
        log.warning(
            f"{self}: Table '{table_name}' has {len(comparison['only_in_df2'])} columns not in schema: {comparison['only_in_df2']}")
        log.warning(f"{self}: These columns exist in the database but not in your schema definition")
        log.warning(f"{self}: Options: 1) Add them to schema, 2) Manually drop them, 3) Ignore if legacy data")

    log.info(f"{self}: Committing schema changes to database...")
    self.commit(table_name)
    log.success(f"{self}: Schema migration completed for table '{table_name}'")
