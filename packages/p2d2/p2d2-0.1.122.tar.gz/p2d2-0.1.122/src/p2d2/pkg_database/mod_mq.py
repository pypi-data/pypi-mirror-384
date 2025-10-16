import atexit
import signal
import sys
import traceback
import uuid
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from typing import Any

from . import Database, Create, Read, Update, Delete
from .mod_mq_models import (
    Message, IState, StatefulQueue,
    IJobTypes, IExecutor, IDatabaseMessageQueue
)

from loguru import logger as log


class State(IState):
    def __init__(self, path: Path = Path.cwd()):
        self.path = path
        self.queue = StatefulQueue(path)
        self.response_queues = {}

    def __repr__(self):
        return f"[{self.path.name}.Queue]"

    def put(self, message: Message) -> dict:
        try:
            if message.job_type is None: raise ValueError(f"Message must have a job type, got {message} instead")
            if message.kwargs is None: raise ValueError(f"Message must have kwargs, got {message} instead")

            self.queue.put(message)
            return {"success": True, "error": ""}

        except Exception as e:
            log.error(f"Error putting message into queue: {e}")
            return {"success": False, "error": e}

    def get(self) -> Message | None:
        if not self.queue.empty():
            message = self.queue.get()
            if not isinstance(message, Message): raise TypeError(
                f"Message is not of type Message, got {type(message)} instead")
            return message
        return None

    def create_response_queue(self, message_id: str) -> Queue:
        response_queue = Queue()
        self.response_queues[message_id] = response_queue
        return response_queue

    def send_response(self, message_id: str, result: Any, error: Exception = None):
        if message_id in self.response_queues:
            self.response_queues[message_id].put({
                "result": result,
                "error": error,
                "success": error is None
            })

    def cleanup_response_queue(self, message_id: str):
        if message_id in self.response_queues:
            del self.response_queues[message_id]


class JobTypes(IJobTypes):
    def __init__(self, jobs_list: list[type | Create | Read | Update | Delete]):
        self.jobs_list = jobs_list
        if len(jobs_list) == 0: raise AttributeError("No jobs registered")
        self.job_map = {job.__name__.lower(): job for job in jobs_list}

    def job_type_to_class(self, job_type: str) -> type | Create | Read | Update | Delete:
        if job_type in self.job_map:
            return self.job_map[job_type]
        raise ValueError(
            f"Job type '{job_type}' not found in registered jobs. Select one of the following\n {self.job_map.keys()}:")


class Executor(IExecutor):
    def __init__(self, database: Database, state: State, job_types: JobTypes):
        self.database = database
        self.state = state
        self.job_types = job_types
        self._running = True
        self._stop_event = Event()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def __repr__(self):
        return f"[{self.database.name}.Executor]"

    def _signal_handler(self, signum, frame):
        log.debug(f"Received signal {signum}, stopping executor")
        self.stop()

    def start(self):
        if not self._running:
            self._running = True
            self._stop_event.clear()
            self._thread = Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self._running:
            self._running = False
            self._stop_event.set()
            if self._thread:
                self._thread.join()

    def _run_loop(self):
        try:
            while self._running:
                message = self.state.get()
                if message:
                    message_id = getattr(message, 'message_id', None)
                    try:
                        log.debug(f"{self}: Executing job '{message_id}' of '{message.job_type}' type with kwargs {message.kwargs}")
                        result = self.execute_job_from_message(message)

                        if message_id:
                            self.state.send_response(message_id, result)

                    except Exception as e:
                        log.error(f"Error executing job {message.job_type}: {e}")
                        if message_id:
                            self.state.send_response(message_id, None, e)
                else:
                    self._stop_event.wait(timeout=1.0)
        except Exception as e:
            log.critical(f"Fatal error in executor thread: {e}")
            log.exception("Full traceback:")
            self._running = False

    def execute_job_from_message(self, message: Message):
        try:
            job_class = self.job_types.job_type_to_class(message.job_type)
            job_kwargs = message.kwargs | {"database": self.database}
            job_instance = job_class(**job_kwargs)

            if hasattr(job_instance, 'execute'):
                return job_instance.execute()
            elif callable(job_instance):
                return job_instance()

        except Exception as e:
            log.error(f"Error executing job {message.job_type}: {e}")
            log.exception("Full traceback:")
            raise


class DatabaseMessageQueue(IDatabaseMessageQueue):
    def __init__(self, database: Database, executor: type[Executor], state: type[State],
                 jobs_list: list[type | Create | Read | Update | Delete]):
        self.database = database
        self.state = state(path=database.cwd.cwd / "message_queue.pkl")
        self.job_types = JobTypes(jobs_list)
        self.executor = executor(self.database, self.state, self.job_types)

    def __repr__(self):
        return f"[{self.database.name}.MessageQueue]"

    def new_message(self, job_type: str, **kwargs):
        if not isinstance((timeout := kwargs.pop("timeout", 30)), int):
            raise TypeError(f"Timeout must be an int, got {type(timeout)} instead")

        message_id = str(uuid.uuid4())
        response_queue = self.state.create_response_queue(message_id)

        message_kwargs = {
            "message_id": message_id,
            "job_type": job_type,
            "kwargs": kwargs,
        }

        result = self.state.put(Message(**message_kwargs))
        if not result["success"]:
            self.state.cleanup_response_queue(message_id)
            return {"success": False, "error": result["error"], "result": None}

        try:
            response = response_queue.get(timeout=timeout)
            return response
        except Empty:
            log.error(f"Timeout waiting for response from job '{job_type}'")
            return {"success": False, "error": "Timeout", "result": None}
        finally:
            self.state.cleanup_response_queue(message_id)