import re
from pathlib import Path
from typing import Optional

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
        body = _process_drawio_macros(body, page, output_dir, confluence)

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


def _process_drawio_macros(
    html: str,
    page: Page,
    output_dir: Path,
    confluence: Confluence,
) -> str:
    """Replace draw.io macros with image references and download PNGs."""
    diagram_names = _extract_drawio_diagram_names(html)
    if not diagram_names:
        return html

    attachments = fetch_attachments(confluence, page.id)

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
        return f'<img src="{png_attachment.title}" alt="{diagram_name}" />'

    return macro_pattern.sub(_replace_macro, html)


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Replace characters that are problematic in filenames
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    # Collapse multiple dashes/spaces
    name = re.sub(r"-+", "-", name)
    name = name.strip("- ")
    return name or "untitled"
