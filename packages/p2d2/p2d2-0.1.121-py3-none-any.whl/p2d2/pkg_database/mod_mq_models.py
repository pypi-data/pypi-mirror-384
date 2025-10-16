import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue

from annotated_dict import AnnotatedDict

from . import Database, Create, Read, Update, Delete

class Message(AnnotatedDict):
    message_id: str
    job_type: str
    kwargs: dict

class StatefulQueue(Queue):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.path.touch(exist_ok=True)

    def fetch(self) -> Queue:
        pickle.load(self.path)

    def commit(self) -> None:
        pickle.dump(self, self.path)

class IState(ABC):
    def __init__(self, path: Path = Path.cwd()):
        pass

    def put(self, message: Message) -> None:
        pass

    def get(self) -> Message | None:
        pass


class IJobTypes(ABC):
    def __init__(self, jobs_list: list[type | Create | Read | Update | Delete]):
        self.jobs_list = jobs_list

    def job_type_to_class(self, job_type: str) -> type:
        pass

class IExecutor(ABC):
    def __init__(self, state: IState, job_types: IJobTypes):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def execute_job_from_message(self, message: Message):
        pass

class IDatabaseMessageQueue(ABC):
    def __init__(self, database: Database, executor: IExecutor, state: IState):
        pass

    @abstractmethod
    def new_message(self, job_type: str, **kwargs):
        pass