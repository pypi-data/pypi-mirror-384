import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

from gitme.storage import MessageStorage


class TestMessageStorage:
    """Test the MessageStorage class with new provider/model metadata."""
    
    def test_save_message_with_provider_metadata(self):
        """Test saving message with provider and model metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / ".gitme"
            storage_file = storage_dir / "messages.json"
            
            with patch.object(MessageStorage, 'storage_dir', storage_dir), \
                 patch.object(MessageStorage, 'storage_file', storage_file):
                
                storage = MessageStorage()
                file_changes = {"test.py": "diff content"}
                
                # Test with Anthropic provider
                storage.save_message(
                    message="Test commit message",
                    repo_path="/test/repo",
                    file_changes=file_changes,
                    provider="anthropic",
                    model="claude-3-7-sonnet-20250219"
                )
                
                # Verify the file was created and contains metadata
                assert storage_file.exists()
                
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                
                assert len(data) == 1
                entry = data[0]
                
                assert entry["message"] == "Test commit message"
                assert entry["repo_path"] == "/test/repo"
                assert entry["file_changes"] == file_changes
                assert entry["provider"] == "anthropic"
                assert entry["model"] == "claude-3-7-sonnet-20250219"
                assert "timestamp" in entry
    
    def test_save_message_with_openai_provider(self):
        """Test saving message with OpenAI provider metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / ".gitme"
            storage_file = storage_dir / "messages.json"
            
            with patch.object(MessageStorage, 'storage_dir', storage_dir), \
                 patch.object(MessageStorage, 'storage_file', storage_file):
                
                storage = MessageStorage()
                file_changes = {"auth.py": "authentication changes"}
                
                # Test with OpenAI provider
                storage.save_message(
                    message="Fix authentication bug",
                    repo_path="/test/auth-repo",
                    file_changes=file_changes,
                    provider="openai",
                    model="gpt-4o-mini"
                )
                
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                
                entry = data[0]
                assert entry["provider"] == "openai"
                assert entry["model"] == "gpt-4o-mini"
    
    def test_save_message_with_defaults(self):
        """Test saving message with default provider values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / ".gitme"
            storage_file = storage_dir / "messages.json"
            
            with patch.object(MessageStorage, 'storage_dir', storage_dir), \
                 patch.object(MessageStorage, 'storage_file', storage_file):
                
                storage = MessageStorage()
                
                # Test with default parameters (should default to anthropic)
                storage.save_message(
                    message="Default provider test",
                    repo_path="/test/repo",
                    file_changes={"test.py": "changes"}
                )
                
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                
                entry = data[0]
                assert entry["provider"] == "anthropic"  # default
                assert entry["model"] is None  # default
    
    def test_multiple_providers_in_history(self):
        """Test storing messages from different providers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / ".gitme"
            storage_file = storage_dir / "messages.json"
            
            with patch.object(MessageStorage, 'storage_dir', storage_dir), \
                 patch.object(MessageStorage, 'storage_file', storage_file):
                
                storage = MessageStorage()
                
                # Save message with Anthropic
                storage.save_message(
                    message="Anthropic message",
                    repo_path="/test/repo",
                    file_changes={"file1.py": "changes"},
                    provider="anthropic",
                    model="claude-3-haiku-20240307"
                )
                
                # Save message with OpenAI
                storage.save_message(
                    message="OpenAI message",
                    repo_path="/test/repo", 
                    file_changes={"file2.py": "changes"},
                    provider="openai",
                    model="gpt-4"
                )
                
                messages = storage.get_messages("/test/repo")
                assert len(messages) == 2
                
                # Verify both providers are stored
                providers = [msg["provider"] for msg in messages]
                models = [msg["model"] for msg in messages]
                
                assert "anthropic" in providers
                assert "openai" in providers
                assert "claude-3-haiku-20240307" in models
                assert "gpt-4" in models
    
    def test_get_messages_includes_metadata(self):
        """Test that retrieved messages include provider metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / ".gitme"
            storage_file = storage_dir / "messages.json"
            
            with patch.object(MessageStorage, 'storage_dir', storage_dir), \
                 patch.object(MessageStorage, 'storage_file', storage_file):
                
                storage = MessageStorage()
                
                storage.save_message(
                    message="Test message",
                    repo_path="/test/repo",
                    file_changes={"test.py": "content"},
                    provider="openai",
                    model="gpt-4o-mini"
                )
                
                messages = storage.get_messages("/test/repo")
                assert len(messages) == 1
                
                message = messages[0]
                assert message["provider"] == "openai"
                assert message["model"] == "gpt-4o-mini"
                assert message["message"] == "Test message"
    
    def test_backward_compatibility(self):
        """Test that old messages without metadata still work."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / ".gitme"
            storage_file = storage_dir / "messages.json"
            
            # Create old-format message manually
            old_message = {
                "timestamp": datetime.now().isoformat(),
                "repo_path": "/test/repo",
                "message": "Old format message",
                "file_changes": {"old.py": "changes"}
                # No provider/model fields
            }
            
            storage_dir.mkdir(exist_ok=True)
            with open(storage_file, 'w') as f:
                json.dump([old_message], f)
            
            with patch.object(MessageStorage, 'storage_dir', storage_dir), \
                 patch.object(MessageStorage, 'storage_file', storage_file):
                
                storage = MessageStorage()
                messages = storage.get_messages("/test/repo")
                
                assert len(messages) == 1
                message = messages[0]
                assert message["message"] == "Old format message"
                # These should not exist in old format
                assert "provider" not in message
                assert "model" not in message