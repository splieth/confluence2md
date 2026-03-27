from dataclasses import dataclass, field
from typing import Any

from atlassian import Confluence

from .config import ConfluenceConfig


@dataclass
class Page:
    id: str
    title: str
    space_key: str
    body: str = ""
    labels: list[str] = field(default_factory=list)
    url: str = ""
    version: int = 1
    parent_title: str = ""


def connect(config: ConfluenceConfig) -> Confluence:
    """Create an authenticated Confluence client."""
    if config.username:
        return Confluence(  # type: ignore[no-untyped-call]
            url=config.url,
            username=config.username,
            password=config.token,
        )
    return Confluence(url=config.url, token=config.token)  # type: ignore[no-untyped-call]


def fetch_page(confluence: Confluence, page_id: str) -> Page:
    """Fetch a single page by ID."""
    raw = confluence.get_page_by_id(  # type: ignore[no-untyped-call]
        page_id,
        expand="body.storage,version,metadata.labels,ancestors",
    )
    return _resolve_page(raw, confluence)


def fetch_pages_by_cql(
    confluence: Confluence,
    cql: str,
    max_results: int = 50,
) -> list[Page]:
    """Fetch pages matching a CQL query."""
    results = confluence.cql(cql, limit=max_results)  # type: ignore[no-untyped-call]
    pages = []
    for item in results.get("results", []):
        content = item.get("content", item)
        page_id = content.get("id", item.get("id"))
        if page_id:
            pages.append(fetch_page(confluence, str(page_id)))
    return pages


def fetch_pages_by_space(
    confluence: Confluence,
    space_key: str,
    max_results: int = 50,
) -> list[Page]:
    """Fetch all pages in a space."""
    raw_pages = confluence.get_all_pages_from_space(  # type: ignore[no-untyped-call]
        space_key,
        start=0,
        limit=max_results,
        expand="body.storage,version,metadata.labels,ancestors",
    )
    return [_resolve_page(raw, confluence) for raw in raw_pages]


def fetch_child_pages(confluence: Confluence, page_id: str) -> list[Page]:
    """Fetch direct child pages of a given page."""
    children = confluence.get_page_child_by_type(  # type: ignore[no-untyped-call]
        page_id,
        type="page",
        expand="body.storage,version,metadata.labels,ancestors",
    )
    return [_resolve_page(child, confluence) for child in children]


def _resolve_page(raw: dict[str, Any], confluence: Confluence) -> Page:
    """Convert a raw Confluence API response into a Page dataclass."""
    page_id = str(raw.get("id", ""))
    title = raw.get("title", "")
    space_key = _extract_space_key(raw)
    body = _extract_body(raw)
    labels = _extract_labels(raw)
    url = _build_page_url(raw, confluence)
    version = _extract_version(raw)
    parent_title = _extract_parent_title(raw)

    return Page(
        id=page_id,
        title=title,
        space_key=space_key,
        body=body,
        labels=labels,
        url=url,
        version=version,
        parent_title=parent_title,
    )


def _extract_space_key(raw: dict[str, Any]) -> str:
    space = raw.get("space", {})
    if isinstance(space, dict):
        return str(space.get("key", ""))
    return ""


def _extract_body(raw: dict[str, Any]) -> str:
    body = raw.get("body", {})
    if isinstance(body, dict):
        storage = body.get("storage", {})
        if isinstance(storage, dict):
            return str(storage.get("value", ""))
    return ""


def _extract_labels(raw: dict[str, Any]) -> list[str]:
    metadata = raw.get("metadata", {})
    if not isinstance(metadata, dict):
        return []
    labels_data = metadata.get("labels", {})
    if not isinstance(labels_data, dict):
        return []
    results = labels_data.get("results", [])
    return [label.get("name", "") for label in results if label.get("name")]


def _extract_version(raw: dict[str, Any]) -> int:
    version = raw.get("version", {})
    if isinstance(version, dict):
        return int(version.get("number", 1))
    return 1


def _extract_parent_title(raw: dict[str, Any]) -> str:
    ancestors = raw.get("ancestors", [])
    if ancestors:
        return str(ancestors[-1].get("title", ""))
    return ""


def _build_page_url(raw: dict[str, Any], confluence: Confluence) -> str:
    links = raw.get("_links", {})
    if isinstance(links, dict):
        webui = links.get("webui", "")
        if webui:
            base = links.get("base", confluence.url.rstrip("/"))
            return f"{base}{webui}"
    return ""
