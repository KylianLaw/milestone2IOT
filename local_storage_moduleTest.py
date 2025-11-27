# local_storage_module.py
import json
from datetime import datetime
from pathlib import Path
import logging

log = logging.getLogger("local_storage")


class LocalStorageTest:
    """
    Save data to local JSON Lines files with daily rotation.
    One file per category per day:
      <base_dir>/<category>_YYYY-MM-DD.jsonl
    """

    def __init__(self, base_dir: str = "local_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _current_file_path(self, category: str) -> Path:
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{category}_{today_str}.jsonl"
        return self.base_dir / filename

    def save(self, category: str, payload: dict):
        try:
            path = self._current_file_path(category)
            data = dict(payload)
            data.setdefault("saved_at", datetime.now().isoformat())
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(data))
                f.write("\n")
            log.debug("Saved %s sample to %s", category, path)
        except Exception as e:
            log.error("Failed to save local data for %s: %s", category, e, exc_info=True)
