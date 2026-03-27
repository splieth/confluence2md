# confluence2md

> Export Confluence pages to Markdown files because using Confluence (or any other Atlassian product for that matter, like [Jira](https://github.com/splieth/jira2md/)) sucks. Works as a CLI tool and as a Python library.

## Installation

```bash
uv sync
```

## Configuration

Copy `config.yaml.example` to `config.yaml` and adjust it to your Confluence instance:

```yaml
confluence:
  url: https://your-instance.atlassian.net/wiki
  token: your-personal-access-token
  username: your-email@example.com

output:
  directory: ./export
  filename_pattern: "{title}"
  include_children: false
  include_labels: true
  include_metadata: true
```

The token can also be set via the `CONFLUENCE2MD_TOKEN` environment variable. The username can be set via `CONFLUENCE2MD_USERNAME`.

For **Confluence Cloud**, both `username` (your email) and `token` (API token) are required. For **Confluence Server/Data Center** with personal access tokens, only `token` is needed.

## CLI Usage

Export pages matching a CQL query:

```bash
confluence2md export --cql "space = DEV AND label = api"
```

Export a single page by ID:

```bash
confluence2md export --page-id 12345
```

Export a page and its children:

```bash
confluence2md export --page-id 12345 --include-children
```

Export all pages from a space:

```bash
confluence2md export --space DEV
```

Override the output directory:

```bash
confluence2md export --cql "space = DEV" --output-dir ./docs
```

Use a specific config file:

```bash
confluence2md -c path/to/config.yaml export --space DEV
```

List available spaces:

```bash
confluence2md list-spaces
confluence2md list-spaces --search "dev"
```

## Library Usage

```python
from confluence2md import load_config, connect, fetch_pages_by_cql, export_pages

config = load_config("config.yaml")
confluence = connect(config.confluence)
pages = fetch_pages_by_cql(confluence, "space = DEV", max_results=100)
paths = export_pages(pages, config.output)
```

You can also render Markdown without writing files:

```python
from confluence2md import render_page

markdown = render_page(page, config.output)
print(markdown)
```

## Releasing

```bash
./scripts/release.sh patch  # 0.1.0 → 0.1.1
./scripts/release.sh minor  # 0.1.0 → 0.2.0
./scripts/release.sh major  # 0.1.0 → 1.0.0
```

This bumps the version in `pyproject.toml`, commits, tags, and pushes. The push triggers a GitHub Actions workflow that publishes the package to PyPI.

## License

MIT
