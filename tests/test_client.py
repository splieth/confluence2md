from unittest.mock import MagicMock

from confluence2md.client import (
    _extract_body,
    _extract_labels,
    _extract_parent_title,
    _extract_space_key,
    _extract_version,
    _resolve_page,
)


def _make_raw_page(
    page_id: str = "12345",
    title: str = "Test Page",
    space_key: str = "DEV",
    body: str = "<p>Hello world</p>",
    labels: list[str] | None = None,
    version: int = 1,
    parent_title: str = "",
) -> dict:
    """Helper to build a fake raw Confluence page response."""
    raw: dict = {
        "id": page_id,
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": body}},
        "version": {"number": version},
        "metadata": {
            "labels": {
                "results": [{"name": label} for label in (labels or [])],
            }
        },
        "ancestors": [],
        "_links": {
            "webui": f"/spaces/{space_key}/pages/{page_id}",
            "base": "https://wiki.example.com",
        },
    }
    if parent_title:
        raw["ancestors"] = [{"title": parent_title}]
    return raw


# --- extraction helpers ---


def test_extract_space_key():
    raw = {"space": {"key": "DEV"}}
    assert _extract_space_key(raw) == "DEV"


def test_extract_space_key_missing():
    assert _extract_space_key({}) == ""


def test_extract_body():
    raw = {"body": {"storage": {"value": "<p>Content</p>"}}}
    assert _extract_body(raw) == "<p>Content</p>"


def test_extract_body_missing():
    assert _extract_body({}) == ""


def test_extract_labels():
    raw = {"metadata": {"labels": {"results": [{"name": "draft"}, {"name": "api"}]}}}
    assert _extract_labels(raw) == ["draft", "api"]


def test_extract_labels_empty():
    raw = {"metadata": {"labels": {"results": []}}}
    assert _extract_labels(raw) == []


def test_extract_labels_missing():
    assert _extract_labels({}) == []


def test_extract_version():
    raw = {"version": {"number": 5}}
    assert _extract_version(raw) == 5


def test_extract_version_missing():
    assert _extract_version({}) == 1


def test_extract_parent_title():
    raw = {"ancestors": [{"title": "Grandparent"}, {"title": "Parent"}]}
    assert _extract_parent_title(raw) == "Parent"


def test_extract_parent_title_no_ancestors():
    raw = {"ancestors": []}
    assert _extract_parent_title(raw) == ""


# --- _resolve_page ---


def test_resolve_page_basic():
    # given
    raw = _make_raw_page(
        page_id="100",
        title="My Page",
        space_key="TEAM",
        body="<p>Body content</p>",
    )
    confluence = MagicMock()
    confluence.url = "https://wiki.example.com"

    # when
    page = _resolve_page(raw, confluence)

    # then
    assert page.id == "100"
    assert page.title == "My Page"
    assert page.space_key == "TEAM"
    assert page.body == "<p>Body content</p>"


def test_resolve_page_with_labels():
    # given
    raw = _make_raw_page(labels=["draft", "reviewed"])
    confluence = MagicMock()
    confluence.url = "https://wiki.example.com"

    # when
    page = _resolve_page(raw, confluence)

    # then
    assert page.labels == ["draft", "reviewed"]


def test_resolve_page_with_parent():
    # given
    raw = _make_raw_page(parent_title="Architecture")
    confluence = MagicMock()
    confluence.url = "https://wiki.example.com"

    # when
    page = _resolve_page(raw, confluence)

    # then
    assert page.parent_title == "Architecture"


def test_resolve_page_url():
    # given
    raw = _make_raw_page(page_id="100", space_key="DEV")
    confluence = MagicMock()
    confluence.url = "https://wiki.example.com"

    # when
    page = _resolve_page(raw, confluence)

    # then
    assert page.url == "https://wiki.example.com/spaces/DEV/pages/100"
