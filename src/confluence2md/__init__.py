"""confluence2md - Export Confluence pages to Markdown files."""

from .client import (
    Page,
    connect,
    fetch_child_pages,
    fetch_page,
    fetch_pages_by_cql,
    fetch_pages_by_space,
)
from .config import Config, ConfluenceConfig, OutputConfig, load_config, validate_config
from .renderer import export_page, export_pages, render_page
from .spaces import list_spaces

__all__ = [
    "Config",
    "ConfluenceConfig",
    "OutputConfig",
    "Page",
    "connect",
    "export_page",
    "export_pages",
    "fetch_child_pages",
    "fetch_page",
    "fetch_pages_by_cql",
    "fetch_pages_by_space",
    "list_spaces",
    "load_config",
    "render_page",
    "validate_config",
]
