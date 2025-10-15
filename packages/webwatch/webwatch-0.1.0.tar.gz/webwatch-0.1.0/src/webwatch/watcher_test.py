"""
Unit tests for the watcher module.
"""

import pytest
from pytest_httpx import HTTPXMock

from .watcher import MismatchError, Watcher

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Welcome</h1>
    <div id="content">
        <p>This is the initial content.</p>
        <span class="data">Data 1</span>
    </div>
</body>
</html>
"""

HTML_CHANGED_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Welcome</h1>
    <div id="content">
        <p>This is the MODIFIED content.</p>
        <span class="data">Data 2</span>
    </div>
</body>
</html>
"""

HTML_CHANGED_STRUCTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Welcome</h1>
    <article id="content">
        <p>This is the initial content.</p>
    </article>
    <span class="data">Data 1</span>
</body>
</html>
"""


@pytest.fixture
def watcher():
    """Fixture for a default Watcher instance."""
    return Watcher(url="https://test.com")


def test_watcher_initialization(watcher):
    assert watcher.url == "https://test.com"
    assert watcher.last_hash is None
    assert watcher.xpath_selector == "//body"  # Default


def test_fetch_content_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://test.com", text=HTML_TEMPLATE)
    watcher = Watcher(url="https://test.com")
    content = watcher.fetch_content()
    assert content == HTML_TEMPLATE


def test_fetch_content_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://test.com", status_code=404)
    watcher = Watcher(url="https://test.com")
    with pytest.raises(Exception, match="404 Not Found"):
        watcher.fetch_content()


def test_extract_target_default_body(watcher):
    target = watcher.extract_target(HTML_TEMPLATE)
    assert "<body>" in target
    assert "Welcome" in target


def test_extract_target_css_selector():
    watcher = Watcher(url="https://test.com", css_selector="#content")
    target = watcher.extract_target(HTML_TEMPLATE)
    assert '<div id="content">' in target
    assert "initial content" in target
    assert "Welcome" not in target


def test_extract_target_xpath_selector():
    watcher = Watcher(url="https://test.com", xpath_selector='//div[@id="content"]/p')
    target = watcher.extract_target(HTML_TEMPLATE)
    assert "<p>This is the initial content.</p>" in target
    assert "div" not in target


def test_extract_target_not_found(watcher):
    watcher.css_selector = "#non-existent"
    target = watcher.extract_target(HTML_TEMPLATE)
    assert target is None


def test_hash_content():
    h1 = Watcher.hash_content("hello")
    h2 = Watcher.hash_content("hello")
    h3 = Watcher.hash_content("world")
    assert h1 == h2
    assert h1 != h3


def test_check_first_run(httpx_mock: HTTPXMock, watcher):
    httpx_mock.add_response(url="https://test.com", text=HTML_TEMPLATE)
    watcher.check()  # Should not raise
    assert watcher.last_hash is not None


def test_check_no_change(httpx_mock: HTTPXMock, watcher):
    httpx_mock.add_response(url="https://test.com", text=HTML_TEMPLATE)
    watcher.check()  # First run
    httpx_mock.add_response(url="https://test.com", text=HTML_TEMPLATE)
    watcher.check()  # Second run, no change
    # No exception should be raised


def test_check_with_change(httpx_mock: HTTPXMock, watcher):
    # First request
    httpx_mock.add_response(url="https://test.com", text=HTML_TEMPLATE)
    watcher.check()

    # Second request with different content
    httpx_mock.add_response(url="https://test.com", text=HTML_CHANGED_CONTENT)
    with pytest.raises(MismatchError, match="Content has changed"):
        watcher.check()
