from unittest.mock import MagicMock

from confluence2md.spaces import list_spaces, print_spaces

SAMPLE_SPACES = {
    "results": [
        {"key": "DEV", "name": "Development", "type": "global"},
        {"key": "HR", "name": "Human Resources", "type": "global"},
        {"key": "~john", "name": "John's Space", "type": "personal"},
        {"key": "OPS", "name": "Operations", "type": "global"},
    ]
}


def _make_confluence_mock(spaces: dict) -> MagicMock:
    mock = MagicMock()
    mock.get_all_spaces.return_value = spaces
    return mock


def test_list_spaces_returns_all_sorted():
    # given
    confluence = _make_confluence_mock(SAMPLE_SPACES)

    # when
    result = list_spaces(confluence)

    # then
    names = [s["name"] for s in result]
    assert names == sorted(names)
    assert len(result) == 4


def test_list_spaces_filters_by_search():
    # given
    confluence = _make_confluence_mock(SAMPLE_SPACES)

    # when
    result = list_spaces(confluence, search="dev")

    # then
    assert len(result) == 1
    assert result[0]["key"] == "DEV"


def test_list_spaces_search_no_match():
    # given
    confluence = _make_confluence_mock(SAMPLE_SPACES)

    # when
    result = list_spaces(confluence, search="nonexistent")

    # then
    assert result == []


def test_list_spaces_empty():
    # given
    confluence = _make_confluence_mock({"results": []})

    # when
    result = list_spaces(confluence)

    # then
    assert result == []


def test_print_spaces_empty(capsys):
    # given / when
    print_spaces([])

    # then
    output = capsys.readouterr().out
    assert "No spaces found." in output


def test_print_spaces_formats_table(capsys):
    # given
    spaces = [
        {"key": "DEV", "name": "Development", "type": "global"},
        {"key": "~john", "name": "John's Space", "type": "personal"},
    ]

    # when
    print_spaces(spaces)

    # then
    output = capsys.readouterr().out
    assert "Key" in output
    assert "Name" in output
    assert "Type" in output
    assert "DEV" in output
    assert "Development" in output
