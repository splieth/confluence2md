import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml

DEFAULT_CONFIG_PATHS = [
    "config.yaml",
    "confluence2md.yaml",
]


@dataclass
class ConfluenceConfig:
    url: str = ""
    token: str = ""
    username: str = ""


@dataclass
class OutputConfig:
    directory: str = "./export"
    filename_pattern: str = "{title}"
    include_children: bool = False
    include_labels: bool = True
    include_metadata: bool = True


@dataclass
class Config:
    confluence: ConfluenceConfig = field(default_factory=ConfluenceConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: Optional[str] = None) -> Config:
    """Load configuration from a YAML file.

    Searches in order: explicit path, config.yaml, confluence2md.yaml,
    ~/.config/confluence2md/config.yaml.
    """
    config_path = _resolve_config_path(path)

    if config_path is None:
        config = Config()
        config.confluence.token = os.environ.get("CONFLUENCE2MD_TOKEN", "")
        config.confluence.username = os.environ.get("CONFLUENCE2MD_USERNAME", "")
        return config

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return _parse_config(data)


def _resolve_config_path(explicit_path: Optional[str] = None) -> Optional[str]:
    if explicit_path:
        if not os.path.exists(explicit_path):
            print(f"Config file not found: {explicit_path}", file=sys.stderr)
            sys.exit(1)
        return explicit_path

    for p in DEFAULT_CONFIG_PATHS:
        if os.path.exists(p):
            return p

    home_config = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "confluence2md",
        "config.yaml",
    )
    if os.path.exists(home_config):
        return home_config

    return None


def _parse_config(data: dict[str, Any]) -> Config:
    confluence_data = data.get("confluence", {})
    output_data = data.get("output", {})

    token = confluence_data.get("token", "") or os.environ.get(
        "CONFLUENCE2MD_TOKEN", ""
    )
    username = confluence_data.get("username", "") or os.environ.get(
        "CONFLUENCE2MD_USERNAME", ""
    )

    confluence_config = ConfluenceConfig(
        url=confluence_data.get("url", ""),
        token=token,
        username=username,
    )

    output_config = OutputConfig(
        directory=output_data.get("directory", "./export"),
        filename_pattern=output_data.get("filename_pattern", "{title}"),
        include_children=output_data.get("include_children", False),
        include_labels=output_data.get("include_labels", True),
        include_metadata=output_data.get("include_metadata", True),
    )

    return Config(confluence=confluence_config, output=output_config)


def validate_config(config: Config) -> None:
    """Validate that required config values are present."""
    errors = []
    if not config.confluence.url:
        errors.append("confluence.url is required")
    if not config.confluence.token:
        errors.append(
            "confluence.token is required "
            "(set in config or CONFLUENCE2MD_TOKEN env var)"
        )
    if errors:
        for e in errors:
            print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)
