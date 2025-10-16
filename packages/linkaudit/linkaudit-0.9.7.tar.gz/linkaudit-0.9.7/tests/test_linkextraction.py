import pytest
from linkaudit.markdownhelpers import extract_urls_from_markdown  

# Sample test data
text1 = "Check out [Google](https://www.google.com) and [Wikipedia](https://en.wikipedia.org)"
text2 = "No URLs here, just plain text."
text3 = "Links: [Example](https://example.com) and [FTP](ftp://ftp.example.com)"
text4 = "Contact [Site](https://another.site) or [Email](mailto:test@example.com)"
text5 = "Only one link: [Yet Another](https://yetanother.com)"
text6 = "No Markdown links, but just https://notignored.com in plain text"
text7 = 'The MyST title way for links - Check out [Google](https://www.google.com) and [Wikipedia](https://en.wikipedia.org "Title for link" )'
text8 = "No External links, but internal to an [image](images/nocomplexity.png)"

# Pytest functions
def test_extract_urls_from_markdown1():
    result = extract_urls_from_markdown(text1)
    expected = ['https://www.google.com', 'https://en.wikipedia.org']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown2():
    result = extract_urls_from_markdown(text2)
    expected = []
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown3():
    result = extract_urls_from_markdown(text3)
    expected = ['https://example.com', 'ftp://ftp.example.com']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown4():
    result = extract_urls_from_markdown(text4)
    expected = ['https://another.site']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown5():
    result = extract_urls_from_markdown(text5)
    expected = ['https://yetanother.com']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown6_with_pattern():
    result = extract_urls_from_markdown(text6)
    expected = ['https://notignored.com']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown7_with_pattern():
    result = extract_urls_from_markdown(text7)
    expected = ['https://www.google.com', 'https://en.wikipedia.org']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown5():
    result = extract_urls_from_markdown(text5)
    expected = ['https://yetanother.com']
    assert result == expected, f"Expected {expected}, but got {result}"

def test_extract_urls_from_markdown8():
    result = extract_urls_from_markdown(text8)
    expected = []
    assert result == expected, f"Expected {expected}, but got {result}"

# Optional: Run pytest if this file is executed directly
if __name__ == "__main__":
    pytest.main(["-v"])
    