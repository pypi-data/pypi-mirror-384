from pathlib import Path

import replicate
from replicate.lib._files import FileOutput, AsyncFileOutput
from replicate.lib._predictions_use import URLPath, get_path_url

# Test token for client instantiation
TEST_TOKEN = "test-bearer-token"


def test_get_path_url_with_urlpath():
    """Test get_path_url returns the URL for URLPath instances."""
    url = "https://example.com/test.jpg"
    path_proxy = URLPath(url)

    result = get_path_url(path_proxy)
    assert result == url


def test_get_path_url_with_fileoutput():
    """Test get_path_url returns the URL for FileOutput instances."""
    url = "https://example.com/test.jpg"
    file_output = FileOutput(url, replicate.Replicate(bearer_token=TEST_TOKEN))

    result = get_path_url(file_output)
    assert result == url


def test_get_path_url_with_async_fileoutput():
    """Test get_path_url returns the URL for AsyncFileOutput instances."""
    url = "https://example.com/test.jpg"
    async_file_output = AsyncFileOutput(url, replicate.AsyncReplicate(bearer_token=TEST_TOKEN))

    result = get_path_url(async_file_output)
    assert result == url


def test_get_path_url_with_regular_path():
    """Test get_path_url returns None for regular Path instances."""
    regular_path = Path("test.txt")

    result = get_path_url(regular_path)
    assert result is None


def test_get_path_url_with_object_without_target():
    """Test get_path_url returns None for objects without __url__."""

    # Test with a string
    result = get_path_url("not a path")
    assert result is None

    # Test with a dict
    result = get_path_url({"key": "value"})
    assert result is None

    # Test with None
    result = get_path_url(None)
    assert result is None


def test_get_path_url_module_level_import():
    """Test that get_path_url can be imported at module level."""
    from replicate import get_path_url as module_get_path_url

    url = "https://example.com/test.jpg"
    file_output = FileOutput(url, replicate.Replicate(bearer_token=TEST_TOKEN))

    result = module_get_path_url(file_output)
    assert result == url


def test_get_path_url_direct_module_access():
    """Test that get_path_url can be accessed directly from replicate module."""
    url = "https://example.com/test.jpg"
    file_output = FileOutput(url, replicate.Replicate(bearer_token=TEST_TOKEN))

    result = replicate.get_path_url(file_output)
    assert result == url


def test_fileoutput_has_url_attribute():
    """Test that FileOutput instances have __url__ attribute."""
    url = "https://example.com/test.jpg"
    file_output = FileOutput(url, replicate.Replicate(bearer_token=TEST_TOKEN))

    assert hasattr(file_output, "__url__")
    assert file_output.__url__ == url


def test_async_fileoutput_has_url_attribute():
    """Test that AsyncFileOutput instances have __url__ attribute."""
    url = "https://example.com/test.jpg"
    async_file_output = AsyncFileOutput(url, replicate.AsyncReplicate(bearer_token=TEST_TOKEN))

    assert hasattr(async_file_output, "__url__")
    assert async_file_output.__url__ == url


def test_urlpath_has_url_attribute():
    """Test that URLPath instances have __url__ attribute."""
    url = "https://example.com/test.jpg"
    url_path = URLPath(url)

    assert hasattr(url_path, "__url__")
    assert url_path.__url__ == url
