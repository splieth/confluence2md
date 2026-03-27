import re
from pathlib import Path

from markdownify import markdownify

from .client import Page
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


def export_page(page: Page, config: OutputConfig) -> Path:
    """Export a single page to a Markdown file. Returns the file path."""
    content = render_page(page, config)
    filename = _safe_filename(config.filename_pattern.format(title=page.title)) + ".md"
    output_dir = Path(config.directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def export_pages(pages: list[Page], config: OutputConfig) -> list[Path]:
    """Export multiple pages to Markdown files."""
    return [export_page(page, config) for page in pages]


def _convert_body(html: str) -> str:
    """Convert Confluence storage format (HTML) to Markdown."""
    return markdownify(html, heading_style="ATX", strip=["style"])


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Replace characters that are problematic in filenames
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    # Collapse multiple dashes/spaces
    name = re.sub(r"-+", "-", name)
    name = name.strip("- ")
    return name or "untitled"
