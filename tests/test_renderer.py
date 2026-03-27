from confluence2md.client import Page
from confluence2md.config import OutputConfig
from confluence2md.renderer import _safe_filename, render_page


def test_render_basic_page():
    # given
    page = Page(
        id="100",
        title="Getting Started",
        space_key="DEV",
        body="<p>Welcome to the project.</p>",
        version=3,
    )
    config = OutputConfig()

    # when
    md = render_page(page, config)

    # then
    assert "# Getting Started" in md
    assert "| Space | DEV |" in md
    assert "| Version | 3 |" in md
    assert "Welcome to the project." in md


def test_render_page_with_labels():
    # given
    page = Page(
        id="200",
        title="API Reference",
        space_key="DEV",
        body="<p>Endpoints</p>",
        labels=["api", "docs"],
    )
    config = OutputConfig(include_labels=True)

    # when
    md = render_page(page, config)

    # then
    assert "api, docs" in md


def test_render_page_without_metadata():
    # given
    page = Page(
        id="300",
        title="Simple Page",
        space_key="DEV",
        body="<p>Just content</p>",
    )
    config = OutputConfig(include_metadata=False)

    # when
    md = render_page(page, config)

    # then
    assert "# Simple Page" in md
    assert "| Field |" not in md
    assert "Just content" in md


def test_render_page_with_parent():
    # given
    page = Page(
        id="400",
        title="Child Page",
        space_key="DEV",
        body="<p>Content</p>",
        parent_title="Architecture",
    )
    config = OutputConfig()

    # when
    md = render_page(page, config)

    # then
    assert "| Parent | Architecture |" in md


def test_render_page_empty_body():
    # given
    page = Page(
        id="500",
        title="Empty Page",
        space_key="DEV",
        body="",
    )
    config = OutputConfig()

    # when
    md = render_page(page, config)

    # then
    assert "# Empty Page" in md


def test_render_page_html_conversion():
    # given
    page = Page(
        id="600",
        title="Rich Page",
        space_key="DEV",
        body=(
            "<h2>Section</h2>"
            "<p>Paragraph with <strong>bold</strong> text.</p>"
            "<ul><li>Item 1</li><li>Item 2</li></ul>"
        ),
    )
    config = OutputConfig(include_metadata=False)

    # when
    md = render_page(page, config)

    # then
    assert "## Section" in md
    assert "**bold**" in md
    assert "Item 1" in md


def test_safe_filename_basic():
    assert _safe_filename("My Page Title") == "My Page Title"


def test_safe_filename_special_chars():
    assert _safe_filename('Page: "Test" <draft>') == "Page- -Test- -draft"


def test_safe_filename_empty():
    assert _safe_filename("") == "untitled"


def test_render_page_labels_hidden():
    # given
    page = Page(
        id="700",
        title="No Labels Shown",
        space_key="DEV",
        body="<p>Content</p>",
        labels=["draft"],
    )
    config = OutputConfig(include_labels=False)

    # when
    md = render_page(page, config)

    # then
    assert "| Labels |" not in md
    assert "| Labels | draft |" not in md
