"""
Persistent per-controller preferences for dynamic UI options.

Stores user-chosen option values in ~/.pitchgrid-mapper/controller_prefs.json
keyed by controller device name.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

PREFS_DIR = Path.home() / ".pitchgrid-mapper"
PREFS_FILE = PREFS_DIR / "controller_prefs.json"


class ControllerPreferences:
    """Persist per-controller dynamic option values."""

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if PREFS_FILE.exists():
            try:
                self._data = json.loads(PREFS_FILE.read_text())
            except Exception as e:
                logger.warning(f"Failed to load controller preferences: {e}")
                self._data = {}

    def _save(self):
        try:
            PREFS_DIR.mkdir(parents=True, exist_ok=True)
            PREFS_FILE.write_text(json.dumps(self._data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save controller preferences: {e}")

    def get_option_values(self, controller_name: str) -> Dict[str, Any]:
        """Get all saved option values for a controller."""
        return self._data.get(controller_name, {}).copy()

    def set_option_value(self, controller_name: str, option_name: str, value: Any):
        """Set a single option value and persist."""
        if controller_name not in self._data:
            self._data[controller_name] = {}
        self._data[controller_name][option_name] = value
        self._save()
