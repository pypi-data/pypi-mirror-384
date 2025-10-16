"""Configuration management"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ProfileConfig:
    """Configuration for a single profile"""
    vault_addr: Optional[str] = None
    vault_token: Optional[str] = None
    vault_mount: str = "secret"
    kubectl_context: Optional[str] = None
    kubectl_namespace: Optional[str] = None
    default_format: str = "table"
    theme: str = "default"

    def update_from_env(self):
        """Update from environment variables"""
        if os.getenv("VAULT_ADDR"):
            self.vault_addr = os.getenv("VAULT_ADDR")
        if os.getenv("VAULT_TOKEN"):
            self.vault_token = os.getenv("VAULT_TOKEN")
        if os.getenv("KUBE_NAMESPACE"):
            self.kubectl_namespace = os.getenv("KUBE_NAMESPACE")


@dataclass
class Config:
    """Global configuration manager"""
    config_dir: Path = field(default_factory=lambda: Path.home() / ".config" / "platon")
    config_file: Optional[Path] = None
    profiles: Dict[str, ProfileConfig] = field(default_factory=dict)
    current_profile: str = "default"
    vault_checked: bool = False

    def __post_init__(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if not self.config_file:
            self.config_file = self.config_dir / "config.yaml"

        if self.config_file.exists():
            self.load()
        else:
            self.profiles["default"] = ProfileConfig()
            self.profiles["default"].update_from_env()

    def load(self, config_file: Optional[Path] = None):
        """Load configuration from file"""
        if config_file:
            self.config_file = Path(config_file)

        if not self.config_file.exists():
            return

        with open(self.config_file, "r") as f:
            data = yaml.safe_load(f) or {}

        self.current_profile = data.get("current_profile", "default")
        self.vault_checked = data.get("vault_checked", False)

        profiles_data = data.get("profiles", {})
        for name, profile_data in profiles_data.items():
            self.profiles[name] = ProfileConfig(**profile_data)

        if "default" not in self.profiles:
            self.profiles["default"] = ProfileConfig()

        self.profiles[self.current_profile].update_from_env()

    def save(self):
        """Save configuration to file"""
        data = {
            "current_profile": self.current_profile,
            "vault_checked": self.vault_checked,
            "profiles": {
                name: asdict(profile)
                for name, profile in self.profiles.items()
            },
        }

        with open(self.config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def get_profile(self, name: Optional[str] = None) -> ProfileConfig:
        """Get profile by name or current"""
        profile_name = name or self.current_profile

        if profile_name not in self.profiles:
            self.profiles[profile_name] = ProfileConfig()

        return self.profiles[profile_name]

    def set_profile(self, name: str):
        """Set current profile"""
        if name not in self.profiles:
            self.profiles[name] = ProfileConfig()

        self.current_profile = name
        self.save()

    def list_profiles(self) -> Dict[str, ProfileConfig]:
        """List all profiles"""
        return self.profiles

    def delete_profile(self, name: str):
        """Delete a profile"""
        if name == "default":
            raise ValueError("Cannot delete default profile")

        if name in self.profiles:
            del self.profiles[name]

            if self.current_profile == name:
                self.current_profile = "default"

            self.save()

    def get_local_config(self) -> Optional[Dict[str, Any]]:
        """Load local .platon.yaml if it exists"""
        local_config = Path.cwd() / ".platon.yaml"

        if local_config.exists():
            with open(local_config, "r") as f:
                return yaml.safe_load(f) or {}

        return None
