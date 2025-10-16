from abc import ABC, abstractmethod
from pathlib import Path
from . import Database


class ICronJob(ABC):
    def __init__(self, interval: int, function: callable):
        self.interval = interval
        self.function = function

    @abstractmethod
    def execute(self, database: Database):
        """This method executes the found function with target database as its argument."""
        pass

class ICronLoader(ABC):
    def __init__(self, path: Path):
        self.path = path
        self.bytes = {}
        self.jobs = []

    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def watcher_loop(self):
        """This method watches the path for changes in bytes in the globbed .py files, triggering self.refresh(), to update the jobs."""
        pass


class ICronManager(ABC):
    def __init__(self, database: Database, cron_loader: type[ICronLoader]):
        self.database = database
        self.cron_loader = cron_loader(self.database.path.parent / "cron_jobs")

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def on_refresh(self):
        """This method is called when the cron_loader refreshes."""
        pass

    @abstractmethod
    def schedule_loop(self):
        """This method continually looks for changes, and if there are no changes, executes the cron jobs according to whether their interval has elapsed."""
        pass
