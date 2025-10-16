"""
License GPL3
(C) 2024-2025 Created by Maikel Mardjan - https://nocomplexity.com/

Help functions for dealing with markdown files, especially MyST.

"""

import re
import os


def extract_urls_from_markdown(markdown_text):
    """
    Extracts all URLs from a Markdown or MyST Markdown file, including multiple URLs in a single line.

    Parameters:
        markdown_text (str): The content of the Markdown file.

    Returns:
        list: A list of extracted URLs.
    """
    # Regular expression to match multiple URL patterns
    url_pattern = re.compile(
        r"\[.*?\]\((https?://[^\s)\"]+|[^)\s\"]+)(?:\s+\"[^\"]*\")?\)"  # Markdown links with titles or without
        r'|(?<!\()(?<!\[)(https?://[^\s)<"]+)'  # Bare URLs (not inside markdown links), avoid ending quotes
        r'|<a\s+[^>]*href=["\'](https?://[^"\'>]+)["\']'  # URLs inside <a href="">
        r'|`[^`]+?\s*<\s*(https?://[^>\s"]+)\s*>`__'  # reStructuredText (reST) links, avoid trailing "
        r'|<\s*(https?://[^\s>"]+)\s*>'  # URLs enclosed in angle brackets, avoid trailing "
        r'|(?:href|src)=["\'](https?://[^"\'>]+)["\']'  # Generic href/src attributes in HTML
        r'|(?<=[:\s])["\']?(https?://[^\s"\'\]]+)["\']?'  # Handles URLs enclosed in quotes after a key like repository_url
        r"|(?<!\w)(https?://[^\s,()]+)"  # Capture standalone URLs, excluding trailing parentheses or commas
    )

    # Extract all matches
    matches = url_pattern.findall(markdown_text)

    # Since findall() returns tuples, flatten and remove empty strings
    urls = [url for match in matches for url in match if url]

    # Filter out internal URLs (relative paths, single words, etc.)
    external_urls = []
    for url in urls:
        # Keep URLs with http/https protocol
        if url.startswith(("http://", "https://")):
            external_urls.append(url)
        # Keep URLs that look external but don't have protocol specified
        elif (
            "." in url
            and not url.startswith((".", "/", "#"))
            and not url.endswith((".md", ".markdown", ".rst", ".txt"))
            and "/" in url
            and not url.startswith(("../", "./", "images/"))
        ):
            external_urls.append(url)

    # Remove trailing dot from each URL
    cleaned_urls = [url.rstrip(".") for url in external_urls]
    return cleaned_urls


def get_links_in_markdown_file(file_path):
    """Checks all URLs in a markdown file"""
    line_url_mapping = []  # List to store tuples of (line_number, url)
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        # Loop through each line and search for URLs
        for line_number, line in enumerate(lines, start=1):
            urls = extract_urls_from_markdown(line)
            for url in urls:
                line_url_mapping.append((line_number, url))
    combined = []
    for line_number, url in line_url_mapping:
        combined.append(
            {"line_number": line_number, "url": url, "status": "Not Checked."}
        )
    return combined


def collect_markdown_files(directory):
    """
    Collects all Markdown files (.md) from a directory, including subdirectories,
    while skipping directories named '_build', '_static', and any directories
    starting with a dot (e.g., '.git', '.env').

    Args:
        directory (str): The path to the directory to search.

    Returns:
        list: A list of paths to Markdown files.
    """
    markdown_files = []
    for root, dirs, files in os.walk(directory):
        # Skip directories named '_build', '_static', and any directory starting with a dot
        dirs[:] = [
            d
            for d in dirs
            if not (
                d.startswith(".") or d == "_build" or d == "_static" or d == "images"
            )
        ]
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files


def create_markdown_table(data):
    """
    Creates a markdown table from a list of dictionaries.

    Args:
        data (list of dicts): A list of dictionaries with 'line_number', 'url', and 'status' keys.

    Returns:
        str: A markdown table string.
    """

    if not data:
        return ""  # Return empty string if data is empty
    header = "| Line Number | URL | Status Code |"
    separator = "|---|---|---|"
    rows = []
    for entry in data:
        row = f"| {entry['line_number']} | {entry['url']} | {entry['status']} |"
        rows.append(row)    
    output = "\n".join([header, separator] + rows)
    return output
