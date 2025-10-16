import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import json
from gitme.git_diff import GitDiffAnalyzer


class TestGitDiffAnalyzer:
    @patch('subprocess.run')
    def test_init(self, mock_run):
        mock_run.return_value = MagicMock()
        analyzer = GitDiffAnalyzer()
        assert analyzer.git_available is True
        assert analyzer.in_git_repo is True
    
    @patch('subprocess.run')
    def test_init_git_not_available(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        analyzer = GitDiffAnalyzer()
        assert analyzer.git_available is False
        assert analyzer.in_git_repo is False
    
    @patch('subprocess.run')
    def test_init_git_available_not_in_repo(self, mock_run):
        # First call succeeds (git --version), second fails (git rev-parse)
        mock_run.side_effect = [MagicMock(), subprocess.CalledProcessError(1, 'git')]
        analyzer = GitDiffAnalyzer()
        assert analyzer.git_available is True
        assert analyzer.in_git_repo is False
    
    def test_check_git_available(self):
        analyzer = GitDiffAnalyzer()
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock()
            result = analyzer._check_git()
            assert result is True
            mock_run.assert_called_once_with(["git", "--version"], capture_output=True, check=True)
    
    def test_check_git_not_available(self):
        analyzer = GitDiffAnalyzer()
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = analyzer._check_git()
            assert result is False
    
    def test_check_git_subprocess_error(self):
        analyzer = GitDiffAnalyzer()
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'git')):
            result = analyzer._check_git()
            assert result is False
    
    @patch('subprocess.run')
    def test_check_git_repo_available(self, mock_run):
        mock_run.return_value = MagicMock()
        analyzer = GitDiffAnalyzer()
        analyzer.git_available = True
        result = analyzer._check_git_repo()
        assert result is True
        # Verify it was called with the right arguments
        calls = [call.args for call in mock_run.call_args_list]
        assert (["git", "rev-parse", "--git-dir"],) in calls
    
    @patch('subprocess.run')
    def test_check_git_repo_not_available(self, mock_run):
        # Initialize with successful git check
        mock_run.return_value = MagicMock()
        analyzer = GitDiffAnalyzer()
        analyzer.git_available = True
        # Now test the repo check failure
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
        result = analyzer._check_git_repo()
        assert result is False
    
    @patch('subprocess.run')
    def test_check_git_repo_when_git_not_available(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        analyzer = GitDiffAnalyzer()
        result = analyzer._check_git_repo()
        assert result is False
    
    def test_run_git_command_success(self):
        analyzer = GitDiffAnalyzer()
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "test output"
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = analyzer._run_git_command(["status"])
            assert result == "test output"
            mock_run.assert_called_once_with(
                ["git", "status"],
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_run_git_command_failure(self):
        analyzer = GitDiffAnalyzer()
        error = subprocess.CalledProcessError(1, 'git')
        error.stderr = "error message"
        
        with patch('subprocess.run', side_effect=error):
            with patch('builtins.print') as mock_print:
                result = analyzer._run_git_command(["status"])
                assert result is None
                mock_print.assert_called_once_with("Git command failed: error message")
    
    def test_get_staged_diff(self):
        analyzer = GitDiffAnalyzer()
        with patch.object(analyzer, '_run_git_command', return_value="staged diff content") as mock_run:
            result = analyzer.get_staged_diff()
            assert result == "staged diff content"
            mock_run.assert_called_once_with(["diff", "--staged"])
    
    def test_get_all_diff(self):
        analyzer = GitDiffAnalyzer()
        with patch.object(analyzer, '_run_git_command', return_value="all diff content") as mock_run:
            result = analyzer.get_all_diff()
            assert result == "all diff content"
            mock_run.assert_called_once_with(["diff", "HEAD"])
    
    def test_get_file_changes_staged(self):
        analyzer = GitDiffAnalyzer()
        status_output = "M\tfile1.py\nA\tfile2.py"
        
        with patch.object(analyzer, '_run_git_command') as mock_run:
            mock_run.side_effect = [
                status_output,  # First call for status
                "diff content for file1",  # Diff for file1
                "diff content for file2"   # Diff for file2
            ]
            
            result = analyzer.get_file_changes(staged_only=True)
            
            assert result == {
                "file1.py": "diff content for file1",
                "file2.py": "diff content for file2"
            }
            
            # Verify the calls
            expected_calls = [
                call(["diff", "--name-status", "--staged"]),
                call(["diff", "--staged", "--", "file1.py"]),
                call(["diff", "--staged", "--", "file2.py"])
            ]
            mock_run.assert_has_calls(expected_calls)
    
    def test_get_file_changes_all(self):
        analyzer = GitDiffAnalyzer()
        status_output = "M\tfile1.py"
        
        with patch.object(analyzer, '_run_git_command') as mock_run:
            mock_run.side_effect = [
                status_output,
                "diff content for file1"
            ]
            
            result = analyzer.get_file_changes(staged_only=False)
            
            assert result == {"file1.py": "diff content for file1"}
            
            expected_calls = [
                call(["diff", "--name-status", "HEAD"]),
                call(["diff", "HEAD", "--", "file1.py"])
            ]
            mock_run.assert_has_calls(expected_calls)
    
    def test_get_file_changes_empty_status(self):
        analyzer = GitDiffAnalyzer()
        
        with patch.object(analyzer, '_run_git_command', return_value=None):
            result = analyzer.get_file_changes()
            assert result == {}
    
    def test_get_file_changes_malformed_status(self):
        analyzer = GitDiffAnalyzer()
        status_output = "M\tfile1.py\nINVALID_LINE\nA\tfile2.py"
        
        with patch.object(analyzer, '_run_git_command') as mock_run:
            mock_run.side_effect = [
                status_output,
                "diff content for file1",
                "diff content for file2"
            ]
            
            result = analyzer.get_file_changes()
            
            # Should only process valid lines
            assert result == {
                "file1.py": "diff content for file1",
                "file2.py": "diff content for file2"
            }
    
    def test_get_file_changes_diff_failure(self):
        analyzer = GitDiffAnalyzer()
        status_output = "M\tfile1.py\nA\tfile2.py"
        
        with patch.object(analyzer, '_run_git_command') as mock_run:
            mock_run.side_effect = [
                status_output,
                None,  # Diff fails for file1
                "diff content for file2"
            ]
            
            result = analyzer.get_file_changes()
            
            # Should only include successful diffs
            assert result == {"file2.py": "diff content for file2"}
    
    def test_format_changes_json(self):
        analyzer = GitDiffAnalyzer()
        test_changes = {'file.py': 'diff content', 'file2.py': 'more diff'}
        
        with patch.object(analyzer, 'get_file_changes', return_value=test_changes):
            result = analyzer.format_changes_json()
            
            # Verify it's valid JSON
            parsed = json.loads(result)
            assert parsed == test_changes
            
            # Verify formatting
            assert '"file.py": "diff content"' in result
            assert '"file2.py": "more diff"' in result
    
    def test_format_changes_json_not_staged(self):
        analyzer = GitDiffAnalyzer()
        test_changes = {'file.py': 'diff content'}
        
        with patch.object(analyzer, 'get_file_changes', return_value=test_changes) as mock_get:
            result = analyzer.format_changes_json(staged_only=False)
            
            mock_get.assert_called_once_with(False)
            parsed = json.loads(result)
            assert parsed == test_changes
    
    def test_format_changes_json_empty(self):
        analyzer = GitDiffAnalyzer()
        
        with patch.object(analyzer, 'get_file_changes', return_value={}):
            result = analyzer.format_changes_json()
            assert result == "{}"