import pandas as pd
import pytest


def python_to_dtype(python_type: type[str | int | float | bool | dict | list]) -> str:
    type_mapping = {
        str: 'object',
        int: 'int64',
        float: 'float64',
        bool: 'bool',
        dict: 'object',
        list: 'object',
    }
    return type_mapping.get(python_type, 'object')


def dtype_to_sql_type(dtype: str) -> str:
    mapping = {
        'int64': 'INTEGER',
        'float64': 'REAL',
        'bool': 'INTEGER',
        'object': 'TEXT',
    }
    return mapping.get(dtype, 'TEXT')


def python_to_sql_type(python_type: type[str | int | float | bool | dict | list]) -> str:
    dtype = python_to_dtype(python_type)
    return dtype_to_sql_type(dtype)


class Table:
    _unique_keys: list = []
    _default_columns: dict = {"created_at": str, "created_by": str, "modified_at": str, "modified_by": str}

    @classmethod
    def get_columns(cls) -> dict[str, type]:
        return {**cls._default_columns, **cls.__annotations__}

    @classmethod
    def get_column_names(cls) -> list[str]:
        return list(cls.get_columns().keys())

    @classmethod
    def get_unique_keys(cls) -> list[str]:
        return cls._unique_keys

    @classmethod
    def get_column_dtypes(cls) -> dict[str, str]:
        return {col: python_to_dtype(col_type) for col, col_type in cls.get_columns().items()}

    @classmethod
    def to_dataframe(cls) -> pd.DataFrame:
        return pd.DataFrame(columns=cls.get_column_names()).astype(cls.get_column_dtypes())


class Schema:
    @classmethod
    def get_tables(cls) -> dict[str, type[Table]]:
        return {name: table_type for name, table_type in cls.__annotations__.items() if not name.startswith("_")}

    @classmethod
    def get_table_names(cls) -> list[str]:
        return list(cls.get_tables().keys())

    @classmethod
    def initialize_dataframes(cls) -> dict[str, pd.DataFrame]:
        return {name: table_type.to_dataframe() for name, table_type in cls.get_tables().items()}

@pytest.fixture()
def dummy_table():
    class DummyTable(Table):
        _unique_keys = ["foo"]
        foo: str
        bar: int

    return DummyTable

@pytest.fixture()
def dummy_schema():
    class Company(Table):
        _unique_keys = ["name"]
        name: str
        employees: int

    class Employee(Table):
        _unique_keys = ["email"]
        name: str
        email: str
        company: str

    class DummySchema(Schema):
        company: Company
        employee: Employee

    return DummySchema


def test_table(dummy_table):
    assert dummy_table._unique_keys == ["foo"]
    assert dummy_table._default_columns == {"created_at": str, "created_by": str, "modified_at": str,
                                            "modified_by": str}
    assert dummy_table.__annotations__ == {"foo": str, "bar": int}
    assert dummy_table.get_column_names() == ["created_at", "created_by", "modified_at", "modified_by", "foo", "bar"]
    df = dummy_table.to_dataframe()
    assert list(df.columns) == ["created_at", "created_by", "modified_at", "modified_by", "foo", "bar"]


def test_schema(dummy_schema):
    tables = dummy_schema.get_tables()
    assert "company" in tables
    assert "employee" in tables
    assert dummy_schema.get_table_names() == ["company", "employee"]

    dfs = dummy_schema.initialize_dataframes()
    assert "company" in dfs
    assert "employee" in dfs
    assert isinstance(dfs["company"], pd.DataFrame)