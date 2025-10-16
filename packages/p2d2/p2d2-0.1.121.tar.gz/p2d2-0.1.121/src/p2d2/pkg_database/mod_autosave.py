AUTOSAVE = """
from loguru import logger as log

def auto_save(database):
    log.info(f"{database}: Attempting to auto-save database...")
    try:
        database.commit_all()
    except Exception as e:
        log.error(f"Error saving database: {e}")
    log.info(f"{database}: Database auto-saved successfully!")

INTERVAL = 120
FUNCTION = auto_save
"""