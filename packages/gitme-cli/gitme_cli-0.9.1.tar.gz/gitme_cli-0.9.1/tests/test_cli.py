import pytest
from unittest.mock import patch, MagicMock
import os
from click.testing import CliRunner
from gitme.cli import cli, generate


class TestCLI:
    """Test the CLI functionality with provider selection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_version(self):
        """Test version flag."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'gitme version' in result.output
    
    def test_cli_help(self):
        """Test help output includes new provider option."""
        result = self.runner.invoke(cli, ['generate', '--help'])
        assert result.exit_code == 0
        assert '--provider' in result.output
        assert 'anthropic' in result.output
        assert 'openai' in result.output
    
    @patch('gitme.cli.GitDiffAnalyzer')
    @patch('gitme.cli.CommitMessageGenerator')
    @patch('gitme.cli.MessageStorage')
    def test_generate_default_anthropic(self, mock_storage, mock_generator_class, mock_analyzer_class):
        """Test default behavior uses Anthropic provider."""
        # Setup mocks
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff content'}
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_generator = MagicMock()
        mock_generator.generate_commit_message.return_value = 'Test commit message'
        mock_generator_class.return_value = mock_generator
        
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            result = self.runner.invoke(generate)
            
            assert result.exit_code == 0
            assert 'Generated commit message:' in result.output
            assert 'Test commit message' in result.output
            
            # Verify Anthropic generator was used
            mock_generator_class.assert_called_once()
            mock_generator.generate_commit_message.assert_called_once()
    
    @patch('gitme.cli.GitDiffAnalyzer')
    @patch('gitme.cli.CommitMessageGenerator')
    @patch('gitme.cli.MessageStorage')
    def test_generate_openai_provider(self, mock_storage, mock_generator_class, mock_analyzer_class):
        """Test using OpenAI provider."""
        # Setup mocks
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff content'}
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_generator_class.generate_commit_message_openai.return_value = 'OpenAI commit message'
        
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test-key'}):
            result = self.runner.invoke(generate, ['--provider', 'openai'])
            
            assert result.exit_code == 0
            assert 'Generated commit message:' in result.output
            assert 'OpenAI commit message' in result.output
            
            # Verify OpenAI class method was used
            mock_generator_class.generate_commit_message_openai.assert_called_once_with(
                file_changes={'test.py': 'diff content'},
                model='gpt-4o-mini'  # Default should switch to OpenAI model
            )
    
    @patch('gitme.cli.GitDiffAnalyzer')
    @patch('gitme.cli.CommitMessageGenerator')
    @patch('gitme.cli.MessageStorage')
    def test_generate_openai_custom_model(self, mock_storage, mock_generator_class, mock_analyzer_class):
        """Test using OpenAI provider with custom model."""
        # Setup mocks
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff content'}
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_generator_class.generate_commit_message_openai.return_value = 'GPT-4 commit message'
        
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test-key'}):
            result = self.runner.invoke(generate, ['--provider', 'openai', '--model', 'gpt-4'])
            
            assert result.exit_code == 0
            assert 'GPT-4 commit message' in result.output
            
            # Verify custom model was used
            mock_generator_class.generate_commit_message_openai.assert_called_once_with(
                file_changes={'test.py': 'diff content'},
                model='gpt-4'
            )
    
    @patch('gitme.cli.GitDiffAnalyzer')
    @patch('gitme.cli.CommitMessageGenerator')
    @patch('gitme.cli.MessageStorage')
    def test_generate_anthropic_custom_model(self, mock_storage, mock_generator_class, mock_analyzer_class):
        """Test using Anthropic provider with custom model."""
        # Setup mocks
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff content'}
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_generator = MagicMock()
        mock_generator.generate_commit_message.return_value = 'Custom Claude message'
        mock_generator_class.return_value = mock_generator
        
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            result = self.runner.invoke(generate, ['--model', 'claude-3-haiku-20240307'])
            
            assert result.exit_code == 0
            assert 'Custom Claude message' in result.output
            
            # Verify custom model was set
            assert mock_generator.model == 'claude-3-haiku-20240307'
    
    @patch('gitme.cli.GitDiffAnalyzer')
    def test_generate_no_git(self, mock_analyzer_class):
        """Test behavior when git is not available."""
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = False
        mock_analyzer_class.return_value = mock_analyzer
        
        result = self.runner.invoke(generate)
        
        assert result.exit_code == 0
        assert 'Error: Git is not installed' in result.output
    
    @patch('gitme.cli.GitDiffAnalyzer')
    def test_generate_not_git_repo(self, mock_analyzer_class):
        """Test behavior when not in a git repository."""
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = False
        mock_analyzer_class.return_value = mock_analyzer
        
        result = self.runner.invoke(generate)
        
        assert result.exit_code == 0
        assert 'Error: Not in a git repository' in result.output
    
    @patch('gitme.cli.GitDiffAnalyzer')
    @patch('gitme.cli.CommitMessageGenerator')
    def test_generate_no_changes(self, mock_generator_class, mock_analyzer_class):
        """Test behavior when no changes are detected."""
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {}
        mock_analyzer_class.return_value = mock_analyzer
        
        result = self.runner.invoke(generate)
        
        assert result.exit_code == 0
        assert 'No changes detected to analyze' in result.output
    
    @patch('gitme.cli.GitDiffAnalyzer')
    def test_generate_anthropic_no_api_key(self, mock_analyzer_class):
        """Test error when Anthropic API key is missing."""
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff'}
        mock_analyzer_class.return_value = mock_analyzer
        
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(generate)
            
            assert result.exit_code == 0
            assert 'Error:' in result.output
            assert 'ANTHROPIC_API_KEY' in result.output
    
    @patch('gitme.cli.GitDiffAnalyzer')
    def test_generate_openai_no_api_key(self, mock_analyzer_class):
        """Test error when OpenAI API key is missing."""
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff'}
        mock_analyzer_class.return_value = mock_analyzer
        
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(generate, ['--provider', 'openai'])
            
            assert result.exit_code == 0
            assert 'Error:' in result.output
            assert 'OPENAI_API_KEY' in result.output
    
    def test_generate_conflicting_flags(self):
        """Test error when using conflicting --staged and --all flags."""
        result = self.runner.invoke(generate, ['--staged', '--all'])
        
        assert result.exit_code == 0
        assert 'Cannot use both --staged and --all options together' in result.output
    
    @patch('gitme.cli.GitDiffAnalyzer')
    @patch('gitme.cli.CommitMessageGenerator')
    @patch('gitme.cli.MessageStorage')
    @patch('subprocess.run')
    def test_generate_with_commit(self, mock_subprocess, mock_storage, mock_generator_class, mock_analyzer_class):
        """Test generating commit message and creating commit."""
        # Setup mocks
        mock_analyzer = MagicMock()
        mock_analyzer.git_available = True
        mock_analyzer.in_git_repo = True
        mock_analyzer.get_untracked_files.return_value = []
        mock_analyzer.get_file_changes.return_value = {'test.py': 'diff content'}
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_generator = MagicMock()
        mock_generator.generate_commit_message.return_value = 'Auto commit message'
        mock_generator_class.return_value = mock_generator
        
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        mock_subprocess.return_value = MagicMock()
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            result = self.runner.invoke(generate, ['--commit'], input='y\n')
            
            assert result.exit_code == 0
            assert 'Auto commit message' in result.output
            assert 'Commit created successfully!' in result.output
            
            # Verify git commit was called
            mock_subprocess.assert_called_with(
                ['git', 'commit', '-a', '-m', 'Auto commit message'],
                check=True
            )