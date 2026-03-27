from unittest.mock import MagicMock, patch

from confluence2md.client import Attachment, Page
from confluence2md.config import OutputConfig
from confluence2md.renderer import (
    _extract_drawio_diagram_names,
    _find_drawio_png,
    _process_drawio_macros,
    _safe_filename,
    export_page,
    render_page,
)


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


# --- draw.io support ---

DRAWIO_MACRO = (
    '<ac:structured-macro ac:name="drawio" ac:schema-version="1">'
    '<ac:parameter ac:name="diagramName">Architecture</ac:parameter>'
    '<ac:parameter ac:name="width">800</ac:parameter>'
    "</ac:structured-macro>"
)

DRAWIO_MACRO_TWO = (
    '<ac:structured-macro ac:name="drawio" ac:schema-version="1">'
    '<ac:parameter ac:name="diagramName">Flow</ac:parameter>'
    "</ac:structured-macro>"
)


def test_extract_drawio_diagram_names_single():
    html = f"<p>Before</p>{DRAWIO_MACRO}<p>After</p>"
    assert _extract_drawio_diagram_names(html) == ["Architecture"]


def test_extract_drawio_diagram_names_multiple():
    html = f"{DRAWIO_MACRO}<p>text</p>{DRAWIO_MACRO_TWO}"
    assert _extract_drawio_diagram_names(html) == ["Architecture", "Flow"]


def test_extract_drawio_diagram_names_none():
    html = "<p>No diagrams here</p>"
    assert _extract_drawio_diagram_names(html) == []


def test_find_drawio_png_direct_match():
    attachments = [
        Attachment(
            id="1",
            title="Architecture.png",
            media_type="image/png",
            download_url="/download/1",
        ),
        Attachment(
            id="2",
            title="other.pdf",
            media_type="application/pdf",
            download_url="/download/2",
        ),
    ]
    result = _find_drawio_png("Architecture", attachments)
    assert result is not None
    assert result.title == "Architecture.png"


def test_find_drawio_png_drawio_suffix():
    attachments = [
        Attachment(
            id="1",
            title="Architecture.drawio.png",
            media_type="image/png",
            download_url="/download/1",
        ),
    ]
    result = _find_drawio_png("Architecture", attachments)
    assert result is not None
    assert result.title == "Architecture.drawio.png"


def test_find_drawio_png_no_match():
    attachments = [
        Attachment(
            id="1",
            title="unrelated.png",
            media_type="image/png",
            download_url="/download/1",
        ),
    ]
    result = _find_drawio_png("Architecture", attachments)
    assert result is None


@patch("confluence2md.renderer.download_attachment")
@patch("confluence2md.renderer.fetch_attachments")
def test_process_drawio_macros(mock_fetch, mock_download):
    # given
    mock_fetch.return_value = [
        Attachment(
            id="1",
            title="Architecture.png",
            media_type="image/png",
            download_url="/download/1",
        ),
    ]
    page = Page(id="100", title="Test", space_key="DEV")
    html = f"<p>Before</p>{DRAWIO_MACRO}<p>After</p>"
    confluence = MagicMock()

    # when
    result = _process_drawio_macros(html, page, MagicMock(), confluence)

    # then
    assert '<img src="Architecture.png" alt="Architecture" />' in result
    assert "<ac:structured-macro" not in result
    assert "<p>Before</p>" in result
    assert "<p>After</p>" in result
    mock_download.assert_called_once()


@patch("confluence2md.renderer.download_attachment")
@patch("confluence2md.renderer.fetch_attachments")
def test_process_drawio_macros_no_png_leaves_macro(mock_fetch, mock_download):
    # given
    mock_fetch.return_value = []
    page = Page(id="100", title="Test", space_key="DEV")
    html = f"<p>Before</p>{DRAWIO_MACRO}<p>After</p>"
    confluence = MagicMock()

    # when
    result = _process_drawio_macros(html, page, MagicMock(), confluence)

    # then
    assert "<ac:structured-macro" in result
    mock_download.assert_not_called()


@patch("confluence2md.renderer.download_attachment")
@patch("confluence2md.renderer.fetch_attachments")
def test_export_page_with_drawio(mock_fetch, mock_download, tmp_path):
    # given
    mock_fetch.return_value = [
        Attachment(
            id="1",
            title="Architecture.png",
            media_type="image/png",
            download_url="/download/1",
        ),
    ]
    page = Page(
        id="100",
        title="Diagrams",
        space_key="DEV",
        body=f"<p>Intro</p>{DRAWIO_MACRO}",
    )
    config = OutputConfig(directory=str(tmp_path), include_metadata=False)
    confluence = MagicMock()

    # when
    path = export_page(page, config, confluence)

    # then
    content = path.read_text()
    assert "![Architecture](Architecture.png)" in content
    mock_download.assert_called_once()
