import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class MessageStorage:
    def __init__(self):
        self.storage_dir = Path.home() / ".gitme"
        self.storage_file = self.storage_dir / "messages.json"
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_message(self, message: str, repo_path: str, file_changes: Dict, provider: str = "anthropic", model: str = None) -> None:
        messages = self._load_messages()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "repo_path": repo_path,
            "message": message,
            "file_changes": file_changes,
            "provider": provider,
            "model": model
        }
        
        messages.append(entry)
        
        # Keep only last 100 messages
        if len(messages) > 100:
            messages = messages[-100:]
        
        with open(self.storage_file, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def get_messages(self, repo_path: Optional[str] = None, limit: int = 10) -> List[Dict]:
        messages = self._load_messages()
        
        if repo_path:
            messages = [m for m in messages if m["repo_path"] == repo_path]
        
        return messages[-limit:]
    
    def clear_messages(self, repo_path: Optional[str] = None) -> None:
        if not repo_path:
            # Clear all messages
            if self.storage_file.exists():
                self.storage_file.unlink()
        else:
            # Clear messages for specific repo
            messages = self._load_messages()
            messages = [m for m in messages if m["repo_path"] != repo_path]
            with open(self.storage_file, 'w') as f:
                json.dump(messages, f, indent=2)
    
    def _load_messages(self) -> List[Dict]:
        if not self.storage_file.exists():
            return []
        
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []