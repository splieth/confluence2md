import argparse
import sys
from typing import Optional

from .config import Config, load_config, validate_config


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="confluence2md",
        description="Export Confluence pages to Markdown files",
    )
    parser.add_argument("--config", "-c", help="Path to config file")

    subparsers = parser.add_subparsers(dest="command")

    # export command
    export_parser = subparsers.add_parser("export", help="Export pages to Markdown")
    export_group = export_parser.add_mutually_exclusive_group(required=True)
    export_group.add_argument("--cql", help="CQL query to select pages")
    export_group.add_argument("--page-id", help="Single page ID")
    export_group.add_argument("--space", help="Export all pages from a space")
    export_parser.add_argument(
        "--output-dir",
        "-o",
        help="Output directory (overrides config)",
    )
    export_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of pages to fetch (default: 50)",
    )
    export_parser.add_argument(
        "--include-children",
        action="store_true",
        help="Also export child pages (when using --page-id)",
    )

    # list-spaces command
    spaces_parser = subparsers.add_parser(
        "list-spaces", help="List available Confluence spaces"
    )
    spaces_parser.add_argument(
        "--search",
        "-s",
        help="Filter spaces by name (case-insensitive)",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config(args.config)

    if args.command == "export":
        _handle_export(args, config)
    elif args.command == "list-spaces":
        _handle_list_spaces(args, config)


def _handle_export(args: argparse.Namespace, config: Config) -> None:
    validate_config(config)

    if args.output_dir:
        config.output.directory = args.output_dir

    from .client import (
        connect,
        fetch_child_pages,
        fetch_page,
        fetch_pages_by_cql,
        fetch_pages_by_space,
    )
    from .renderer import export_page, export_pages

    confluence = connect(config.confluence)

    if args.page_id:
        page = fetch_page(confluence, args.page_id)
        path = export_page(page, config.output, confluence)
        print(f"Exported: {path}")

        include_children = args.include_children or config.output.include_children
        if include_children:
            children = fetch_child_pages(confluence, args.page_id)
            if children:
                child_paths = export_pages(children, config.output, confluence)
                for p in child_paths:
                    print(f"Exported: {p}")
                total = 1 + len(child_paths)
                print(f"\n{total} page(s) exported to {config.output.directory}")
            else:
                print(f"\n1 page exported to {config.output.directory}")
    elif args.space:
        pages = fetch_pages_by_space(confluence, args.space, args.max_results)
        if not pages:
            print("No pages found.")
            return
        paths = export_pages(pages, config.output, confluence)
        for p in paths:
            print(f"Exported: {p}")
        print(f"\n{len(paths)} page(s) exported to {config.output.directory}")
    else:
        pages = fetch_pages_by_cql(confluence, args.cql, args.max_results)
        if not pages:
            print("No pages found.")
            return
        paths = export_pages(pages, config.output, confluence)
        for p in paths:
            print(f"Exported: {p}")
        print(f"\n{len(paths)} page(s) exported to {config.output.directory}")


def _handle_list_spaces(args: argparse.Namespace, config: Config) -> None:
    validate_config(config)

    from .client import connect
    from .spaces import list_spaces, print_spaces

    confluence = connect(config.confluence)
    spaces = list_spaces(confluence, search=args.search)
    print_spaces(spaces)
