from abc import abstractmethod, ABC, abstractclassmethod

from starlette.requests import Request
from pandas import DataFrame


class IDatabase(ABC):
    def get_table(self, table_name: str) -> DataFrame:
        pass

    @abstractmethod
    def fetch(self, table_name: str) -> DataFrame:
        pass

    @abstractmethod
    def fetch_all(self) -> dict[str, DataFrame]:
        pass

    @abstractmethod
    def commit(self, table_name: str) -> None:
        pass

    @abstractmethod
    def commit_all(self) -> None:
        pass

class ICreate(ABC):
    def __init__(self, database: IDatabase, table_name: str, signature: str, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def from_request(cls, database: IDatabase, request: Request):
        pass

    def execute(self):
        pass

    @classmethod
    @abstractmethod
    def execute_now(cls, database: IDatabase, table_name: str, signature: str, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def execute_now_from_request(cls, database: IDatabase, request: Request):
        pass

class IRead(ABC):
    def __init__(self, database: IDatabase, table_name: str, signature: str, **conditions):
        pass

    @classmethod
    @abstractmethod
    def from_request(cls, database: IDatabase, request: Request):
        pass

    def execute(self):
        pass

    @classmethod
    @abstractmethod
    def execute_now(cls, database: IDatabase, table_name: str, signature: str, **conditions):
        pass

    @classmethod
    @abstractmethod
    def execute_now_from_request(cls, database: IDatabase, request: Request):
        pass

class IUpdate(ABC):
    def __init__(self, database: IDatabase, table_name: str, signature: str, conditions: dict, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def from_request(cls, database: IDatabase, request: Request):
        pass

    def execute(self):
        pass

    @classmethod
    @abstractmethod
    def execute_now(cls, database: IDatabase, table_name: str, signature: str, conditions: dict, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def execute_now_from_request(cls, database: IDatabase, request: Request):
        pass

class IDelete(ABC):
    def __init__(self, database: IDatabase, table_name: str, signature: str, **conditions):
        pass

    @classmethod
    @abstractmethod
    def from_request(cls, database: IDatabase, request: Request):
        pass

    def execute(self):
        pass

    @classmethod
    @abstractmethod
    def execute_now(cls, database: IDatabase, table_name: str, signature: str, **conditions):
        pass

    @classmethod
    @abstractmethod
    def execute_now_from_request(cls, database: IDatabase, request: Request):
        pass