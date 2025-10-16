import pytest
from unittest.mock import patch, MagicMock
import os
from gitme.llm_client import CommitMessageGenerator


class TestCommitMessageGenerator:
    """Test the CommitMessageGenerator class for both Anthropic and OpenAI providers."""
    
    def test_init_anthropic(self):
        """Test initialization with Anthropic API key."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = CommitMessageGenerator()
            assert generator.api_key == 'test-key'
            assert generator.model == 'claude-3-7-sonnet-20250219'
            assert generator._is_openai is False
    
    def test_init_anthropic_no_key(self):
        """Test initialization without Anthropic API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Anthropic API key is required"):
                CommitMessageGenerator()
    
    def test_init_anthropic_explicit_key(self):
        """Test initialization with explicit Anthropic API key."""
        generator = CommitMessageGenerator(api_key='explicit-key')
        assert generator.api_key == 'explicit-key'
        assert generator._is_openai is False
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', True)
    @patch('gitme.llm_client.OpenAI')
    def test_create_openai_client_default(self, mock_openai_class):
        """Test creating OpenAI client with default settings."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test-key'}):
            generator = CommitMessageGenerator.create_openai_client()
            
            assert generator.api_key == 'openai-test-key'
            assert generator.model == 'gpt-4o-mini'
            assert generator._is_openai is True
            assert generator.client == mock_client
            mock_openai_class.assert_called_once_with(api_key='openai-test-key')
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', True)
    @patch('gitme.llm_client.OpenAI')
    def test_create_openai_client_custom_model(self, mock_openai_class):
        """Test creating OpenAI client with custom model."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test-key'}):
            generator = CommitMessageGenerator.create_openai_client(model='gpt-4')
            
            assert generator.model == 'gpt-4'
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', True)
    def test_create_openai_client_no_key(self):
        """Test creating OpenAI client without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                CommitMessageGenerator.create_openai_client()
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', False)
    def test_create_openai_client_not_available(self):
        """Test creating OpenAI client when library not installed."""
        with pytest.raises(ImportError, match="OpenAI library not installed"):
            CommitMessageGenerator.create_openai_client()
    
    def test_generate_commit_message_anthropic(self):
        """Test generating commit message with Anthropic."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = CommitMessageGenerator()
            
            # Mock Anthropic response
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "Add user authentication feature\n\n- Modified auth.py\n- Updated config.json"
            
            with patch.object(generator.client, 'messages') as mock_messages:
                mock_messages.create.return_value = mock_response
                
                file_changes = {"auth.py": "diff content", "config.json": "more diff"}
                result = generator.generate_commit_message(file_changes)
                
                assert "Add user authentication feature" in result
                assert "Modified auth.py" in result
                mock_messages.create.assert_called_once()
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', True)
    @patch('gitme.llm_client.OpenAI')
    def test_generate_commit_message_openai(self, mock_openai_class):
        """Test generating commit message with OpenAI."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Fix authentication bug\n\n- Fixed auth.py\n- Updated tests"
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test-key'}):
            generator = CommitMessageGenerator.create_openai_client()
            
            file_changes = {"auth.py": "diff content"}
            result = generator.generate_commit_message(file_changes)
            
            assert "Fix authentication bug" in result
            assert "Fixed auth.py" in result
            mock_client.chat.completions.create.assert_called_once()
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', True)
    @patch('gitme.llm_client.OpenAI')
    def test_generate_commit_message_openai_class_method(self, mock_openai_class):
        """Test the class method for generating commit message with OpenAI."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Update documentation\n\n- Updated README.md"
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test-key'}):
            file_changes = {"README.md": "documentation changes"}
            result = CommitMessageGenerator.generate_commit_message_openai(file_changes)
            
            assert "Update documentation" in result
            assert "Updated README.md" in result
            mock_client.chat.completions.create.assert_called_once()
    
    def test_generate_commit_message_no_changes(self):
        """Test generating commit message with no file changes."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = CommitMessageGenerator()
            result = generator.generate_commit_message({})
            assert result == "No changes to commit"
    
    def test_generate_commit_message_anthropic_error(self):
        """Test error handling for Anthropic API calls."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = CommitMessageGenerator()
            
            with patch.object(generator.client, 'messages') as mock_messages:
                mock_messages.create.side_effect = Exception("API Error")
                
                with patch('builtins.print') as mock_print:
                    file_changes = {"test.py": "diff content"}
                    result = generator.generate_commit_message(file_changes)
                    
                    assert result == "Update files"
                    mock_print.assert_called_once_with("Error generating commit message: API Error")
    
    @patch('gitme.llm_client.OPENAI_AVAILABLE', True)
    def test_generate_commit_message_openai_class_method_error(self):
        """Test error handling for OpenAI class method."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                CommitMessageGenerator.generate_commit_message_openai({"test.py": "diff"})
    
    def test_create_prompt(self):
        """Test prompt creation for commit message generation."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = CommitMessageGenerator()
            
            file_changes = {
                "file1.py": "short diff",
                "file2.py": "a" * 1500  # Long diff to test truncation
            }
            
            prompt = generator._create_prompt(file_changes)
            
            assert "Analyze the following git diff" in prompt
            assert "File: file1.py" in prompt
            assert "File: file2.py" in prompt
            assert "short diff" in prompt
            # Long diff should be truncated
            assert prompt.count("a") < 1500
    
    def test_create_prompt_empty_changes(self):
        """Test prompt creation with empty file changes."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            generator = CommitMessageGenerator()
            
            prompt = generator._create_prompt({})
            
            assert "Analyze the following git diff" in prompt
            assert "Git diff:" in prompt