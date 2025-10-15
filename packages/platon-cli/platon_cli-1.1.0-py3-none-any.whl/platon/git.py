"""Git repository detection and path conversion"""

import subprocess
from pathlib import Path
from dataclasses import dataclass


@dataclass
class GitRepo:
    """Git repository information"""
    path: str
    vault_path: str
    namespace: str
    remote_url: str
    
    @classmethod
    def from_cwd(cls):
        """Detect repo from current working directory"""
        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()
            
            # Extract path from git@gitlab.sikt.no:path/to/repo.git
            import re
            match = re.search(r"git@gitlab\.sikt\.no:(.+)\.git", remote_url)
            if not match:
                raise ValueError("Not a Sikt GitLab repository")
            
            repo_path = match.group(1)
            
            # Create vault path and namespace
            vault_path = f"gitlab/{repo_path}"
            namespace = repo_path.replace("/", "-").lower()
            
            return cls(
                path=repo_path,
                vault_path=vault_path,
                namespace=namespace,
                remote_url=remote_url,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError("Not in a git repository")
