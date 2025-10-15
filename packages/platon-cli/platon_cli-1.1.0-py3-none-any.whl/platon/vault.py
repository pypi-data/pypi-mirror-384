"""Vault operations wrapper"""

import subprocess
import json
from typing import Dict, Optional


class VaultManager:
    """Manages Vault operations"""

    def __init__(self, repo):
        self.repo = repo
        self.mount = "secret"

    def _run(self, *args) -> str:
        """Run vault command"""
        cmd = (
            ["vault", "kv"]
            + list(args)
            + ["-mount=" + self.mount, self.repo.vault_path]
        )
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def list_secrets(self) -> Dict[str, str]:
        """Get all secrets"""
        output = self._run("get", "-format=json")
        data = json.loads(output)
        return data.get("data", {}).get("data", {})

    def get_secret(self, key: str) -> Optional[str]:
        """Get specific secret"""
        try:
            output = self._run("get", f"-field={key}")
            return output.strip()
        except subprocess.CalledProcessError:
            return None

    def set_secret(self, key: str, value: str):
        """Set secret"""
        secrets = self.list_secrets()
        secrets[key] = value

        args = []
        for k, v in secrets.items():
            args.append(f"{k}={v}")

        subprocess.run(
            ["vault", "kv", "put", f"-mount={self.mount}", self.repo.vault_path] + args,
            check=True,
        )

    def delete_secret(self, key: str):
        """Delete secret"""
        secrets = self.list_secrets()
        if key in secrets:
            del secrets[key]

            args = []
            for k, v in secrets.items():
                args.append(f"{k}={v}")

            subprocess.run(
                ["vault", "kv", "put", f"-mount={self.mount}", self.repo.vault_path]
                + args,
                check=True,
            )

    def diff_versions(self, v1: Optional[int], v2: Optional[int]) -> str:
        """Diff two versions"""
        try:
            if v1 is None:
                v1 = 1
            if v2 is None:
                output = self._run("get", "-format=json")
                data = json.loads(output)
                v2 = data.get("data", {}).get("metadata", {}).get("version", 1)

            output1 = self._run("get", f"-version={v1}", "-format=json")
            data1 = json.loads(output1)
            secrets1 = data1.get("data", {}).get("data", {})

            output2 = self._run("get", f"-version={v2}", "-format=json")
            data2 = json.loads(output2)
            secrets2 = data2.get("data", {}).get("data", {})

            from .utils import diff_dict
            return diff_dict(secrets1, secrets2)
        except subprocess.CalledProcessError as e:
            return f"Error comparing versions: {e}"

    def import_from_env_file(self, env_file_path: str, merge: bool = True) -> Dict[str, int]:
        """Import secrets from .env file"""
        from dotenv import dotenv_values

        env_vars = dotenv_values(env_file_path)

        if merge:
            existing = self.list_secrets()
            existing.update(env_vars)
            env_vars = existing

        args = [f"{k}={v}" for k, v in env_vars.items()]

        subprocess.run(
            ["vault", "kv", "put", f"-mount={self.mount}", self.repo.vault_path] + args,
            check=True,
        )

        return {
            "imported": len(env_vars),
            "keys": list(env_vars.keys())
        }

    def import_from_file(self, file_path: str, format_type: str, merge: bool = True) -> Dict[str, int]:
        """Import secrets from file in any supported format (json, yaml, env, dotenv)"""
        from .utils import parse_file_to_dict

        data = parse_file_to_dict(file_path, format_type)

        if merge:
            existing = self.list_secrets()
            existing.update(data)
            data = existing

        args = [f"{k}={v}" for k, v in data.items()]

        subprocess.run(
            ["vault", "kv", "put", f"-mount={self.mount}", self.repo.vault_path] + args,
            check=True,
        )

        return {
            "imported": len(data),
            "keys": list(data.keys())
        }

    def health_check(self) -> Dict:
        """Check vault health"""
        try:
            secrets = self.list_secrets()
            return {
                "healthy": True,
                "status": "Connected",
                "secret_count": len(secrets),
                "last_modified": "Recently",  # Could fetch from metadata
            }
        except Exception:
            return {
                "healthy": False,
                "status": "Disconnected",
                "secret_count": 0,
                "last_modified": "Unknown",
            }
