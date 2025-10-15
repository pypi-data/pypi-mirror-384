from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR_ENV = "LAMMY_HOME"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "lammy"
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_IMAGE = "family:gpu-base-24-04"


@dataclass
class LammyConfig:
    """Simple representation of the persisted lammy configuration."""

    api_key: Optional[str] = None
    default_region: Optional[str] = None
    default_ssh_key_name: Optional[str] = None
    default_image: Optional[str] = DEFAULT_IMAGE
    ssh_user: str = "ubuntu"
    ssh_identity_file: Optional[str] = None
    ssh_alias_prefix: str = "lammy"
    last_instance_id: Optional[str] = None
    last_instance_alias: Optional[str] = None
    last_instance_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LammyConfig":
        filtered: Dict[str, Any] = {}
        for field in cls.__dataclass_fields__.keys():  # type: ignore[attr-defined]
            if field in data:
                filtered[field] = data[field]
        return cls(**filtered)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfigManager:
    """Load and persist local lammy CLI configuration."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        config_dir = Path(
            os.environ.get(CONFIG_DIR_ENV, DEFAULT_CONFIG_DIR)
        ).expanduser()
        self.config_path = config_path or (config_dir / DEFAULT_CONFIG_FILE)

    def load(self) -> LammyConfig:
        if not self.config_path.exists():
            return LammyConfig()
        try:
            with self.config_path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return LammyConfig()
        return LammyConfig.from_dict(raw)

    def save(self, config: LammyConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_suffix(".json.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(config.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(tmp_path, self.config_path)
            try:
                os.chmod(self.config_path, 0o600)
            except OSError:
                # It's okay if we cannot adjust permissions (e.g. on Windows).
                pass
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def set_api_key(self, api_key: str) -> LammyConfig:
        config = self.load()
        config.api_key = api_key.strip()
        self.save(config)
        return config

    def update_defaults(
        self,
        *,
        default_region: Optional[str] = None,
        default_ssh_key_name: Optional[str] = None,
        default_image: Optional[str] = None,
        ssh_user: Optional[str] = None,
        ssh_identity_file: Optional[str] = None,
        ssh_alias_prefix: Optional[str] = None,
    ) -> LammyConfig:
        config = self.load()
        if default_region is not None:
            config.default_region = default_region or None
        if default_ssh_key_name is not None:
            config.default_ssh_key_name = default_ssh_key_name or None
        if default_image is not None:
            config.default_image = default_image or None
        if ssh_user is not None:
            config.ssh_user = ssh_user or config.ssh_user
        if ssh_identity_file is not None:
            config.ssh_identity_file = ssh_identity_file or None
        if ssh_alias_prefix is not None:
            config.ssh_alias_prefix = ssh_alias_prefix or config.ssh_alias_prefix
        self.save(config)
        return config

    def remember_instance(
        self,
        *,
        instance_id: str,
        alias: str,
        name: Optional[str] = None,
    ) -> LammyConfig:
        config = self.load()
        config.last_instance_id = instance_id
        config.last_instance_alias = alias
        config.last_instance_name = name
        self.save(config)
        return config

    def clear_last_instance(self) -> LammyConfig:
        config = self.load()
        config.last_instance_id = None
        config.last_instance_alias = None
        config.last_instance_name = None
        self.save(config)
        return config


def read_env_api_key(dotenv_path: Optional[Path] = None) -> Optional[str]:
    """
    Attempt to read a Lambda API key from a .env file or the environment.

    The explicit LAMBDA_API_KEY environment variable always wins.
    """

    env_value = os.environ.get("LAMBDA_API_KEY")
    if env_value:
        return env_value.strip()

    path = dotenv_path or (Path.cwd() / ".env")
    if not path.exists():
        return None

    try:
        contents = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for line in contents:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()
        if not stripped.startswith("LAMBDA_API_KEY="):
            continue
        _, value = stripped.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            return value
    return None
