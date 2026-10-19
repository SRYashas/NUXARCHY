"""
User Profile and Settings Manager
Handles persistent application configuration, telemetry polling intervals,
and default performance & lighting profiles.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class AppSettings:
    polling_interval_ms: int = 1000
    start_minimized: bool = False
    enable_auto_boost: bool = True
    default_performance_profile: str = "balanced"
    default_lighting_profile: str = "Default"
    temperature_unit: str = "C"  # "C" or "F"
    theme: str = "CyberDark"


class ProfileManager:
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or os.path.expanduser("~/.config/nuxarchy")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.settings = self.load_settings()

    def load_settings(self) -> AppSettings:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return AppSettings(**data)
            except Exception:
                pass
        return AppSettings()

    def save_settings(self, settings: AppSettings) -> bool:
        self.settings = settings
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(settings), f, indent=2)
            return True
        except Exception:
            return False
