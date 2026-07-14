import re
from html import escape, unescape
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from atlassian import Confluence
from markdownify import markdownify

from .client import (
    Attachment,
    Page,
    download_attachment,
    fetch_attachments,
)
from .config import OutputConfig


def render_page(page: Page, config: OutputConfig) -> str:
    """Render a single Confluence page as a Markdown string."""
    lines: list[str] = []
    lines.append(f"# {page.title}")
    lines.append("")

    # Metadata table
    if config.include_metadata:
        table_rows: list[tuple[str, str]] = []
        table_rows.append(("Space", page.space_key))
        if page.parent_title:
            table_rows.append(("Parent", page.parent_title))
        if page.url:
            table_rows.append(("URL", page.url))
        table_rows.append(("Version", str(page.version)))
        if config.include_labels and page.labels:
            table_rows.append(("Labels", ", ".join(page.labels)))

        if table_rows:
            lines.append("| Field | Value |")
            lines.append("|-------|-------|")
            for name, value in table_rows:
                lines.append(f"| {name} | {value} |")
            lines.append("")

    # Body content
    if page.body:
        markdown_body = _convert_body(page.body)
        if markdown_body.strip():
            lines.append(markdown_body.strip())
            lines.append("")

    return "\n".join(lines)


def export_page(
    page: Page,
    config: OutputConfig,
    confluence: Optional[Confluence] = None,
) -> Path:
    """Export a single page to a Markdown file. Returns the file path."""
    output_dir = Path(config.directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    body = page.body
    if confluence:
        body = _process_attachment_macros(body, page, output_dir, confluence)

    content = render_page(
        Page(
            id=page.id,
            title=page.title,
            space_key=page.space_key,
            body=body,
            labels=page.labels,
            url=page.url,
            version=page.version,
            parent_title=page.parent_title,
        ),
        config,
    )

    filename = _safe_filename(config.filename_pattern.format(title=page.title)) + ".md"
    filepath = output_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def export_pages(
    pages: list[Page],
    config: OutputConfig,
    confluence: Optional[Confluence] = None,
) -> list[Path]:
    """Export multiple pages to Markdown files."""
    return [export_page(page, config, confluence) for page in pages]


def _convert_body(html: str) -> str:
    """Convert Confluence storage format (HTML) to Markdown."""
    return markdownify(html, heading_style="ATX", strip=["style"])


def _extract_drawio_diagram_names(html: str) -> list[str]:
    """Extract draw.io diagram names from Confluence storage format HTML."""
    names: list[str] = []
    # Confluence macros use ac: namespace prefixes which aren't valid XML
    # without namespace declarations, so we use regex to extract them.
    macro_pattern = re.compile(
        r'<ac:structured-macro[^>]*ac:name=["\']drawio["\'][^>]*>'
        r"(.*?)</ac:structured-macro>",
        re.DOTALL,
    )
    param_pattern = re.compile(
        r'<ac:parameter[^>]*ac:name=["\']diagramName["\'][^>]*>'
        r"(.*?)</ac:parameter>",
        re.DOTALL,
    )
    for macro_match in macro_pattern.finditer(html):
        macro_body = macro_match.group(1)
        param_match = param_pattern.search(macro_body)
        if param_match:
            names.append(param_match.group(1).strip())
    return names


def _find_drawio_png(
    diagram_name: str, attachments: list[Attachment]
) -> Optional[Attachment]:
    """Find the PNG attachment for a draw.io diagram."""
    # draw.io stores previews with various naming conventions
    candidates = [
        f"{diagram_name}.png",
        f"{diagram_name}.drawio.png",
    ]
    for att in attachments:
        if att.title in candidates:
            return att
    return None


def _process_attachment_macros(
    html: str,
    page: Page,
    output_dir: Path,
    confluence: Confluence,
) -> str:
    """Download referenced attachments and rewrite macros as image links.

    Handles both draw.io diagram macros and embedded images (``<ac:image>``).
    Attachments are fetched once and shared between both processors, so pages
    without either kind of macro incur no extra API call.
    """
    has_drawio = bool(_extract_drawio_diagram_names(html))
    has_images = bool(_IMAGE_MACRO_PATTERN.search(html))
    if not (has_drawio or has_images):
        return html

    attachments = fetch_attachments(confluence, page.id)
    if has_drawio:
        html = _process_drawio_macros(html, attachments, output_dir, confluence)
    if has_images:
        html = _process_images(html, attachments, output_dir, confluence)
    return html


def _process_drawio_macros(
    html: str,
    attachments: list[Attachment],
    output_dir: Path,
    confluence: Confluence,
) -> str:
    """Replace draw.io macros with image references and download PNGs."""
    macro_pattern = re.compile(
        r'<ac:structured-macro[^>]*ac:name=["\']drawio["\'][^>]*>'
        r"(.*?)</ac:structured-macro>",
        re.DOTALL,
    )
    param_pattern = re.compile(
        r'<ac:parameter[^>]*ac:name=["\']diagramName["\'][^>]*>'
        r"(.*?)</ac:parameter>",
        re.DOTALL,
    )

    def _replace_macro(match: re.Match[str]) -> str:
        macro_body = match.group(1)
        param_match = param_pattern.search(macro_body)
        if not param_match:
            return match.group(0)

        diagram_name = param_match.group(1).strip()
        png_attachment = _find_drawio_png(diagram_name, attachments)
        if not png_attachment:
            return match.group(0)

        download_attachment(confluence, png_attachment, output_dir)
        return _img_tag(png_attachment.title, diagram_name)

    return macro_pattern.sub(_replace_macro, html)


# Confluence embeds images as <ac:image ...><ri:attachment ri:filename="..."/>
# or <ri:url ri:value="..."/></ac:image>. These aren't valid XML without the
# ac:/ri: namespace declarations, so we match them with regex like the macros.
_IMAGE_MACRO_PATTERN = re.compile(r"<ac:image\b([^>]*)>(.*?)</ac:image>", re.DOTALL)
_ATTACHMENT_FILENAME_PATTERN = re.compile(
    r'<ri:attachment[^>]*\bri:filename=["\']([^"\']+)["\']'
)
_IMAGE_URL_PATTERN = re.compile(r'<ri:url[^>]*\bri:value=["\']([^"\']+)["\']')
_IMAGE_ALT_PATTERN = re.compile(r'\bac:alt=["\']([^"\']*)["\']')


def _process_images(
    html: str,
    attachments: list[Attachment],
    output_dir: Path,
    confluence: Confluence,
) -> str:
    """Replace ``<ac:image>`` macros with ``<img>`` tags.

    Attachment-backed images are downloaded next to the Markdown file and
    referenced locally; images pointing at an external URL are kept as remote
    references. A macro whose attachment cannot be found on the page (for
    example an image attached to a different page) is left untouched.
    """

    def _replace(match: re.Match[str]) -> str:
        attrs, inner = match.group(1), match.group(2)
        alt_match = _IMAGE_ALT_PATTERN.search(attrs)

        filename_match = _ATTACHMENT_FILENAME_PATTERN.search(inner)
        if filename_match:
            filename = unescape(filename_match.group(1))
            attachment = _find_attachment(filename, attachments)
            if attachment is None:
                return match.group(0)
            download_attachment(confluence, attachment, output_dir)
            alt = unescape(alt_match.group(1)) if alt_match else filename
            return _img_tag(attachment.title, alt)

        url_match = _IMAGE_URL_PATTERN.search(inner)
        if url_match:
            url = unescape(url_match.group(1))
            alt = unescape(alt_match.group(1)) if alt_match else ""
            return f'<img src="{escape(url)}" alt="{escape(alt)}" />'

        return match.group(0)

    return _IMAGE_MACRO_PATTERN.sub(_replace, html)


def _find_attachment(
    filename: str, attachments: list[Attachment]
) -> Optional[Attachment]:
    """Find an attachment whose title matches the given filename."""
    for attachment in attachments:
        if attachment.title == filename:
            return attachment
    return None


def _img_tag(src: str, alt: str) -> str:
    """Build an ``<img>`` tag pointing at a locally downloaded attachment.

    The source is URL-encoded so filenames containing spaces or other special
    characters survive the conversion to a Markdown image link.
    """
    return f'<img src="{quote(src)}" alt="{escape(alt)}" />'


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Replace characters that are problematic in filenames
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    # Collapse multiple dashes/spaces
    name = re.sub(r"-+", "-", name)
    name = name.strip("- ")
    return name or "untitled"
