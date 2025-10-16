import subprocess
import json
from typing import Dict, List, Optional


class GitDiffAnalyzer:
    def __init__(self):
        self.git_available = self._check_git()
        self.in_git_repo = self._check_git_repo()
    
    def _check_git(self) -> bool:
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_git_repo(self) -> bool:
        """Check if current directory is inside a git repository"""
        if not self.git_available:
            return False
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _run_git_command(self, args: List[str]) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e.stderr}")
            return None
    
    def get_staged_diff(self) -> Optional[str]:
        return self._run_git_command(["diff", "--staged"])
    
    def get_all_diff(self) -> Optional[str]:
        return self._run_git_command(["diff", "HEAD"])
    
    def get_file_changes(self, staged_only: bool = True) -> Dict[str, str]:
        diff_args = ["diff", "--name-status"]
        if staged_only:
            diff_args.append("--staged")
        else:
            diff_args.append("HEAD")
        
        status_output = self._run_git_command(diff_args)
        if not status_output:
            return {}
        
        file_changes = {}
        for line in status_output.split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    status, filename = parts[0], parts[1]
                    
                    diff_args = ["diff"]
                    if staged_only:
                        diff_args.append("--staged")
                    else:
                        diff_args.append("HEAD")
                    diff_args.append("--")
                    diff_args.append(filename)
                    
                    file_diff = self._run_git_command(diff_args)
                    if file_diff:
                        file_changes[filename] = file_diff
        
        return file_changes
    
    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files in the repository"""
        output = self._run_git_command(["ls-files", "--others", "--exclude-standard"])
        if not output:
            return []
        return [line.strip() for line in output.split('\n') if line.strip()]
    
    def format_changes_json(self, staged_only: bool = True) -> str:
        changes = self.get_file_changes(staged_only)
        return json.dumps(changes, indent=2)