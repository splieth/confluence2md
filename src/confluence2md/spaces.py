from typing import Optional

from atlassian import Confluence


def list_spaces(
    confluence: Confluence, search: Optional[str] = None
) -> list[dict[str, str]]:
    """List available Confluence spaces, optionally filtered by a search term.

    Returns a list of dicts with 'key', 'name', and 'type' keys.
    """
    raw_spaces = confluence.get_all_spaces(start=0, limit=500)  # type: ignore[no-untyped-call]
    results = []
    for space in raw_spaces.get("results", []):
        name = space.get("name", "")
        key = space.get("key", "")
        space_type = space.get("type", "")

        if search and search.lower() not in name.lower():
            continue

        results.append(
            {
                "key": key,
                "name": name,
                "type": space_type,
            }
        )

    results.sort(key=lambda x: x["name"])
    return results


def print_spaces(spaces: list[dict[str, str]]) -> None:
    """Print discovered spaces in a readable table format."""
    if not spaces:
        print("No spaces found.")
        return

    key_width = max(len(s["key"]) for s in spaces)
    name_width = max(len(s["name"]) for s in spaces)
    key_width = max(key_width, 3)
    name_width = max(name_width, 4)

    header = f"{'Key':<{key_width}}  {'Name':<{name_width}}  Type"
    print(header)
    print("-" * len(header))
    for s in spaces:
        print(f"{s['key']:<{key_width}}  {s['name']:<{name_width}}  {s['type']}")
