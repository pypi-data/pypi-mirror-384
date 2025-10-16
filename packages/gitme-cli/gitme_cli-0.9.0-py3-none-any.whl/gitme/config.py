import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".gitme"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "model": "claude-haiku-4-5",
            "max_tokens": 300,
            "temperature": 0.3,
            "staged_only": True
        }
    
    def save_config(self):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save_config()