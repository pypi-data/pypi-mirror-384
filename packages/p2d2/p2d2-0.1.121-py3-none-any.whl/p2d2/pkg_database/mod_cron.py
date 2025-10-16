from pathlib import Path
from threading import Thread, Event
import time
import importlib.util
import sys
import signal
import atexit
import traceback

from loguru import logger as log

from . import Database
from .mod_cron_models import ICronJob, ICronLoader, ICronManager


class CronJob(ICronJob):
    def __init__(self, interval: int, function: callable):
        super().__init__(interval, function)
        self.last_run = time.time()

    def execute(self, database: Database):
        start_time = time.time()
        try:
            self.function(database)
            self.last_run = time.time()
            execution_time = self.last_run - start_time
            log.debug(f"Cron job '{self.function.__name__}' executed successfully in {execution_time:.3f}s")
        except Exception as e:
            execution_time = time.time() - start_time
            log.error(f"Error executing cron job '{self.function.__name__}' after {execution_time:.3f}s: {e}")
            log.exception("Full traceback:")


class CronLoader(ICronLoader):
    def __init__(self, path: Path):
        super().__init__(path)
        self.refresh()
        self._running = True
        self._stop_event = Event()
        self._thread = Thread(target=self.watcher_loop, daemon=True)
        self._thread.start()
        log.success(f"{self}: CronLoader initialized with path: {path}")

        atexit.register(self._cleanup)

    def __repr__(self):
        return f"[{self.path.name}.CronLoader]"

    def _cleanup(self):
        log.debug(f"{self}: CronLoader shutting down")
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def refresh(self):
        log.debug(f"{self}: Starting refresh, current jobs: {len(self.jobs)}")
        self.jobs.clear()

        if not self.path.exists():
            log.warning(f"{self}: Cron path does not exist: {self.path}")
            return

        loaded_count = 0
        for py_file in self.path.glob("*.py"):
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[py_file.stem] = module
                spec.loader.exec_module(module)

                if hasattr(module, 'INTERVAL') and hasattr(module, 'FUNCTION'):
                    interval = module.INTERVAL
                    function = module.FUNCTION
                    job = CronJob(interval, function)
                    self.jobs.append(job)
                    loaded_count += 1
                    log.debug(
                        f"{self}: Loaded cron job '{function.__name__}' from {py_file.name} (interval: {interval}s)")
                else:
                    log.warning(f"{self}: {py_file.name} missing INTERVAL or FUNCTION")
            except Exception as e:
                log.error(f"Error loading cron job {py_file.name}: {e}")
                log.exception("Full traceback:")
                continue

        log.success(f"{self}: Cron refresh complete: {loaded_count} job(s) loaded, total jobs now: {len(self.jobs)}")

    def watcher_loop(self):
        try:
            log.debug(f"{self}: Cron watcher loop started")
            while self._running:
                if not self.path.exists():
                    self._stop_event.wait(timeout=5.0)
                    continue

                current_bytes = {}
                for py_file in self.path.glob("*.py"):
                    try:
                        current_bytes[py_file.name] = py_file.read_bytes()
                    except Exception as e:
                        log.error(f"Error reading {py_file.name}: {e}")

                if current_bytes != self.bytes:
                    log.debug(f"{self}: Cron file changes detected, reloading...")
                    self.bytes = current_bytes
                    self.refresh()

                self._stop_event.wait(timeout=5.0)
        except Exception as e:
            log.critical(f"Fatal error in cron watcher thread: {e}")
            log.exception("Full traceback:")
            self._running = False


class CronManager(ICronManager):
    def __init__(self, database: Database, cron_loader: type[ICronLoader]):
        super().__init__(database, cron_loader)
        self._running = True
        self._stop_event = Event()
        self._thread = Thread(target=self.schedule_loop, daemon=True)
        self._thread.start()
        log.debug(f"{self}: CronManager initialized and started")

        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def __repr__(self):
        return f"[{self.database.name}.CronManager]"

    def _signal_handler(self, signum, frame):
        log.warning(f"{self}: Received signal {signum}, stopping CronManager")
        self.stop()

    def start(self):
        if not self._running:
            self._running = True
            self._stop_event.clear()
            self._thread = Thread(target=self.schedule_loop, daemon=True)
            self._thread.start()
            log.debug(f"{self}: CronManager started")

    def stop(self):
        if self._running:
            log.debug(f"{self}: Stopping CronManager thread")
            self._running = False
            self._stop_event.set()
            if self._thread:
                self._thread.join()
            log.debug(f"{self}: CronManager thread stopped")

    def on_refresh(self):
        pass

    def schedule_loop(self):
        try:
            log.debug(f"{self}: Cron schedule loop started")
            while self._running:
                current_time = time.time()

                # log.debug(f"{self}: Checking {len(self.cron_loader.jobs)} jobs")
                for job in self.cron_loader.jobs:
                    time_since_last = current_time - job.last_run
                    if time_since_last >= job.interval:
                        log.debug(
                            f"{self}: Executing job '{job.function.__name__}' (last run: {time_since_last:.1f}s ago)")
                        job.execute(self.database)

                self._stop_event.wait(timeout=1.0)
        except Exception as e:
            log.critical(f"Fatal error in cron schedule thread: {e}")
            log.exception("Full traceback:")
            self._running = False