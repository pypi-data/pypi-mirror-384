"""Test some basic urls extraction"""

import pytest
from linkaudit import markdownhelpers
import os
import pprint  # pretty print


TEST_FILE = "testfile.md"


def test_get_links_in_markdown_file():
    """Test function for get_links_in_markdown_file."""
    test_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEST_FILE)

    result = markdownhelpers.get_links_in_markdown_file(test_file_path)

    # Ensure the result is printed when running pytest with -s , so pytest -s
    # pprint.pprint(result)

    assert isinstance(result, list), "Output should be a list"
    assert all(
        isinstance(item, dict) for item in result
    ), "Each item should be a dictionary"



@pytest.mark.parametrize(
    "line, expected_urls",
    [
        (
            "This is some text with a URL: https://www.example.com and another one: http://anothersite.org/page?param=value.",
            ["https://www.example.com", "http://anothersite.org/page?param=value"],
        ),
        ("No URLs here.", []),
        (
            "A URL in parentheses: (https://www.google.com/search?q=python) and one with special chars: https://example.com/page#section.",
            [
                "https://www.google.com/search?q=python",
                "https://example.com/page#section",
            ],
        ),
        (
            "A markdown link: [Example](https://www.example.com) and a myst link: [Example](https://www.example.com).",
            ["https://www.example.com", "https://www.example.com"],
        ),
        (
            "URL with port: http://localhost:8000/api/data",
            ["http://localhost:8000/api/data"],
        ),
        (
            '[Jupyter Book](https://jupyterbook.org "JB Homepage") and [Another link](http://anothersite.com)',
            ["https://jupyterbook.org", "http://anothersite.com"],
        ),
        (
            "Mixed: https://google.com [Link1](https://example.net) text http://site.org/page [Link 2](https://anothersite.co.uk 'Title')",
            [
                "https://google.com",
                "https://example.net",
                "http://site.org/page",
                "https://anothersite.co.uk",
            ],
        ),
        ("[Jupyter Book](https://jupyterbook.org)", ["https://jupyterbook.org"]),
        (
            '[Jupyter Book](https://jupyterbook.org "JB Homepage")',
            ["https://jupyterbook.org"],
        ),
        ("https://jupyterbook.org", ["https://jupyterbook.org"]),
        ("http://jupyterbook.org", ["http://jupyterbook.org"]),
        (
            "[NOCX](nocomplexity.com)",  
            [],
        ),
        (
            " pandas can be installed via pip from `PyPI <https://pypi.org/project/pandas>`__.",
            ["https://pypi.org/project/pandas"],
        ),
        (
            "<https://ipycanvas.readthedocs.io/en/latest/>",
            ["https://ipycanvas.readthedocs.io/en/latest/"],
        ),
        (
            ' repository_url: "https://gitlab.com/nocomplexity/simplepub" ',
            ["https://gitlab.com/nocomplexity/simplepub"],
        ),
    ],
)
def test_extract_urls_from_markdown(line, expected_urls):
    """Test function for markdownhelpers.extract_urls_from_markdown."""
    urls_found = markdownhelpers.extract_urls_from_markdown(line)

    print(f"Input: {line}")
    print(f"Extracted URLs: {urls_found}")

    assert urls_found == expected_urls, f"Expected {expected_urls} but got {urls_found}"
