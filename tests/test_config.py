import os
import tempfile

import yaml

from confluence2md.config import _parse_config, load_config


def test_parse_config_minimal():
    # given
    data = {
        "confluence": {
            "url": "https://wiki.example.com",
            "token": "abc123",
        }
    }

    # when
    config = _parse_config(data)

    # then
    assert config.confluence.url == "https://wiki.example.com"
    assert config.confluence.token == "abc123"
    assert config.output.directory == "./export"


def test_parse_config_full():
    # given
    data = {
        "confluence": {
            "url": "https://wiki.example.com",
            "token": "abc123",
            "username": "user@example.com",
        },
        "output": {
            "directory": "./docs",
            "filename_pattern": "{title}",
            "include_children": True,
            "include_labels": True,
            "include_metadata": True,
        },
    }

    # when
    config = _parse_config(data)

    # then
    assert config.confluence.username == "user@example.com"
    assert config.output.directory == "./docs"
    assert config.output.include_children is True


def test_parse_config_token_from_env(monkeypatch):
    # given
    monkeypatch.setenv("CONFLUENCE2MD_TOKEN", "env-token")
    data = {
        "confluence": {
            "url": "https://wiki.example.com",
        }
    }

    # when
    config = _parse_config(data)

    # then
    assert config.confluence.token == "env-token"


def test_parse_config_username_from_env(monkeypatch):
    # given
    monkeypatch.setenv("CONFLUENCE2MD_USERNAME", "env-user")
    data = {
        "confluence": {
            "url": "https://wiki.example.com",
            "token": "abc123",
        }
    }

    # when
    config = _parse_config(data)

    # then
    assert config.confluence.username == "env-user"


def test_load_config_from_file():
    # given
    data = {
        "confluence": {
            "url": "https://wiki.example.com",
            "token": "file-token",
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        f.flush()
        path = f.name

    # when
    config = load_config(path)

    # then
    os.unlink(path)
    assert config.confluence.url == "https://wiki.example.com"
    assert config.confluence.token == "file-token"
