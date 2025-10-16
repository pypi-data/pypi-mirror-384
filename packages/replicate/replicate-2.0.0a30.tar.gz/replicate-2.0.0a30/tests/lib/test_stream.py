"""Tests for the deprecated stream() function."""

from __future__ import annotations

import warnings
from unittest.mock import Mock, patch

import pytest

import replicate
from replicate import Replicate, AsyncReplicate


def test_stream_shows_deprecation_warning():
    """Test that stream() shows a deprecation warning."""
    with patch("replicate.lib._stream.use") as mock_use:
        # Create a mock function that returns an iterator
        mock_function = Mock()
        mock_function.return_value = iter(["Hello", " ", "world"])
        mock_use.return_value = mock_function

        # Call stream and capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            client = Replicate(bearer_token="test-token")
            _ = list(  # pyright: ignore[reportDeprecated]
                client.stream(  # pyright: ignore[reportDeprecated]
                    "anthropic/claude-4.5-sonnet",
                    input={"prompt": "Hello"},
                )
            )

            # Check that deprecation warnings were raised
            assert len(w) > 0
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0

            # Verify the @deprecated decorator message appears
            # (there may be multiple warnings from different decorator levels)
            messages = [str(warning.message) for warning in deprecation_warnings]
            expected_message = "replicate.stream() is deprecated. Use replicate.use() with streaming=True instead"
            assert expected_message in messages


def test_stream_calls_use_with_streaming_true():
    """Test that stream() internally calls use() with streaming=True."""
    with patch("replicate.lib._stream.use") as mock_use:
        # Create a mock function that returns an iterator
        mock_function = Mock()
        mock_function.return_value = iter(["Hello", " ", "world"])
        mock_use.return_value = mock_function

        client = Replicate(bearer_token="test-token")

        # Suppress deprecation warnings for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            _ = list(  # pyright: ignore[reportDeprecated]
                client.stream(  # pyright: ignore[reportDeprecated]
                    "anthropic/claude-4.5-sonnet",
                    input={"prompt": "Hello"},
                )
            )

        # Verify use() was called with streaming=True
        mock_use.assert_called_once()
        call_args = mock_use.call_args
        assert call_args.kwargs["streaming"] is True
        assert call_args.args[1] == "anthropic/claude-4.5-sonnet"

        # Verify the mock function was called with the input
        mock_function.assert_called_once_with(prompt="Hello")


def test_stream_returns_iterator():
    """Test that stream() returns an iterator of strings."""
    with patch("replicate.lib._stream.use") as mock_use:
        # Create a mock function that returns an iterator
        mock_function = Mock()
        mock_function.return_value = iter(["Hello", " ", "world", "!"])
        mock_use.return_value = mock_function

        client = Replicate(bearer_token="test-token")

        # Suppress deprecation warnings for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = client.stream(  # pyright: ignore[reportDeprecated]
                "anthropic/claude-4.5-sonnet",
                input={"prompt": "Say hello"},
            )

        # Verify we get an iterator
        assert hasattr(result, "__iter__")

        # Verify the content
        output = list(result)
        assert output == ["Hello", " ", "world", "!"]


def test_stream_works_same_as_use_with_streaming():
    """Test that stream() produces the same output as use() with streaming=True."""
    with patch("replicate.lib._stream.use") as mock_stream_use, \
         patch("replicate.lib._predictions_use.use") as mock_predictions_use:
        # Create a mock function that returns an iterator
        mock_function = Mock()
        expected_output = ["Test", " ", "output"]
        mock_function.return_value = iter(expected_output.copy())
        mock_stream_use.return_value = mock_function
        mock_predictions_use.return_value = mock_function

        client = Replicate(bearer_token="test-token")

        # Get output from stream()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            stream_output = list(
                client.stream(  # pyright: ignore[reportDeprecated]
                    "test-model",
                    input={"prompt": "test"},
                )
            )

        # Reset the mock
        mock_function.return_value = iter(expected_output.copy())

        # Get output from use() with streaming=True
        model = client.use("test-model", streaming=True)  # pyright: ignore[reportUnknownVariableType]
        use_output = list(model(prompt="test"))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]

        # Verify they produce the same output
        assert stream_output == use_output


def test_module_level_stream_function():
    """Test that the module-level replicate.stream() function works."""
    with patch("replicate.lib._stream.use") as mock_use:
        # Create a mock function that returns an iterator
        mock_function = Mock()
        mock_function.return_value = iter(["a", "b", "c"])
        mock_use.return_value = mock_function

        # Suppress deprecation warnings for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = list(
                replicate.stream(  # pyright: ignore[reportDeprecated]
                    "test-model",
                    input={"prompt": "test"},
                )
            )

        # Verify we got the expected output
        assert result == ["a", "b", "c"]

        # Verify use() was called with streaming=True
        mock_use.assert_called_once()
        assert mock_use.call_args.kwargs["streaming"] is True


@pytest.mark.asyncio
async def test_async_stream_shows_deprecation_warning():
    """Test that async stream() shows a deprecation warning."""
    with patch("replicate.lib._stream.use") as mock_use:
        # Create a mock async function that returns an async iterator
        async def async_gen():
            yield "Hello"
            yield " "
            yield "world"

        mock_function = Mock()
        mock_function.return_value = async_gen()
        mock_use.return_value = mock_function

        # Call stream and capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            client = AsyncReplicate(bearer_token="test-token")
            result = []
            async for item in await client.stream(  # pyright: ignore[reportDeprecated]
                "anthropic/claude-4.5-sonnet",
                input={"prompt": "Hello"},
            ):
                result.append(item)  # pyright: ignore[reportUnknownMemberType]

            # Check that deprecation warnings were raised
            assert len(w) > 0
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0

            # Verify the @deprecated decorator message appears
            messages = [str(warning.message) for warning in deprecation_warnings]
            expected_message = "replicate.stream() is deprecated. Use replicate.use() with streaming=True instead"
            assert expected_message in messages


def test_deprecation_message_includes_example():
    """Test that the detailed deprecation message includes a helpful example."""
    with patch("replicate.lib._stream.use") as mock_use:
        mock_function = Mock()
        mock_function.return_value = iter([])
        mock_use.return_value = mock_function

        client = Replicate(bearer_token="test-token")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            list(
                client.stream(  # pyright: ignore[reportDeprecated]
                    "anthropic/claude-4.5-sonnet",
                    input={"prompt": "Hello", "max_tokens": 100},
                )
            )

            # Find the detailed warning from _format_deprecation_message
            # (should be one of the warnings, as there are multiple deprecation warnings)
            detailed_message = None
            for warning in w:
                msg = str(warning.message)
                if "will be removed in a future version" in msg:
                    detailed_message = msg
                    break

            assert detailed_message is not None, "Expected detailed deprecation message not found"

            # Verify the complete detailed message format
            expected_message = (
                "replicate.stream() is deprecated and will be removed in a future version. "
                "Use replicate.use() with streaming=True instead:\n\n"
                '    model = replicate.use("anthropic/claude-4.5-sonnet", streaming=True)\n'
                "    for event in model(input={\n"
                '        "prompt": "Hello",\n'
                '        "max_tokens": 100,\n'
                "    }):\n"
                '        print(str(event), end="")\n'
            )
            assert detailed_message == expected_message
