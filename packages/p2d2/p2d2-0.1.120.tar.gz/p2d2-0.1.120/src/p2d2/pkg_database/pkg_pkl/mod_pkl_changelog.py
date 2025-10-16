import pickle
from loguru import logger as log

class PickleChangelog:
    def __init__(self, database: 'Database'):
        self.database = database
        self.path = self.database.cwd.file_structure[1]
        self.changelog: dict = {}
        self.fetch()

    def __repr__(self):
        return f"[{self.path.name}]"

    def fetch(self):
        try:
            with open(self.path, 'rb') as f:
                self.changelog = pickle.load(f)
            log.debug(f"{self}: Loaded changelog.")
        except (FileNotFoundError, EOFError):
            log.debug("No existing changelog found or empty file, starting fresh")

    # noinspection PyTypeChecker
    def commit(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self.changelog, f)

    def log_change(self, signature: str, table_name: str, change_type: str):
        if not (sig := self.changelog.get(signature)):
            self.changelog[signature] = sig = {}
        if not (tbl := sig.get(table_name)):
            sig[table_name] = tbl = {}
        if not (chg := tbl.get(change_type)):
            tbl[change_type] = chg = 0
        tbl[change_type] = chg + 1