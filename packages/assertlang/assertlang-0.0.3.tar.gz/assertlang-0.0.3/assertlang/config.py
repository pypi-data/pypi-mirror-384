"""
Promptware configuration management.

Supports global and per-project configuration files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomli
    import tomli_w
    HAS_TOML = True
except ImportError:
    HAS_TOML = False


class Config:
    """Promptware configuration manager."""

    def __init__(self):
        self.global_config_dir = self._get_config_dir()
        self.global_config_file = self.global_config_dir / "config.toml"
        self.project_config_file = Path(".promptware") / "config.toml"

        # Default configuration
        self.defaults = {
            "defaults": {
                "language": "python",
                "template": "basic",
                "output_dir": None,  # None means use generated/<agent-name>
            },
            "generate": {
                "auto_confirm": False,
            },
            "init": {
                "port": 3000,
            },
        }

        # Load config (project overrides global)
        self.config = self._load_config()

    def _get_config_dir(self) -> Path:
        """Get configuration directory following XDG Base Directory spec."""
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            config_dir = Path(xdg_config_home) / "assertlang"
        else:
            config_dir = Path.home() / ".config" / "assertlang"

        return config_dir

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from global and project files."""
        config = self.defaults.copy()

        # Load global config
        if self.global_config_file.exists():
            try:
                if HAS_TOML:
                    with open(self.global_config_file, "rb") as f:
                        global_config = tomli.load(f)
                    self._merge_config(config, global_config)
                else:
                    # Fallback to JSON if tomli not available
                    with open(self.global_config_file, "r") as f:
                        global_config = json.load(f)
                    self._merge_config(config, global_config)
            except Exception:
                pass  # Ignore invalid config files

        # Load project config (overrides global)
        if self.project_config_file.exists():
            try:
                if HAS_TOML:
                    with open(self.project_config_file, "rb") as f:
                        project_config = tomli.load(f)
                    self._merge_config(config, project_config)
                else:
                    with open(self.project_config_file, "r") as f:
                        project_config = json.load(f)
                    self._merge_config(config, project_config)
            except Exception:
                pass

        return config

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Merge override config into base config."""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, project: bool = False):
        """Set configuration value using dot notation."""
        keys = key.split(".")
        config_file = self.project_config_file if project else self.global_config_file

        # Load existing config
        if config_file.exists():
            try:
                if HAS_TOML:
                    with open(config_file, "rb") as f:
                        config = tomli.load(f)
                else:
                    with open(config_file, "r") as f:
                        config = json.load(f)
            except Exception:
                config = {}
        else:
            config = {}

        # Set value
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        # Write config
        config_file.parent.mkdir(parents=True, exist_ok=True)

        if HAS_TOML:
            with open(config_file, "wb") as f:
                tomli_w.dump(config, f)
        else:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

        # Reload config
        self.config = self._load_config()

    def unset(self, key: str, project: bool = False):
        """Remove configuration value."""
        keys = key.split(".")
        config_file = self.project_config_file if project else self.global_config_file

        if not config_file.exists():
            return

        # Load existing config
        try:
            if HAS_TOML:
                with open(config_file, "rb") as f:
                    config = tomli.load(f)
            else:
                with open(config_file, "r") as f:
                    config = json.load(f)
        except Exception:
            return

        # Remove value
        current = config
        for k in keys[:-1]:
            if k not in current:
                return
            current = current[k]

        if keys[-1] in current:
            del current[keys[-1]]

        # Write config
        if HAS_TOML:
            with open(config_file, "wb") as f:
                tomli_w.dump(config, f)
        else:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

        # Reload config
        self.config = self._load_config()

    def list_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config.copy()

    def get_config_file(self, project: bool = False) -> Path:
        """Get path to config file."""
        return self.project_config_file if project else self.global_config_file


# Global instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
