"""Basic tests for strands-deepgram package."""

import pytest


def test_import():
    """Test that the package can be imported."""
    from strands_deepgram import deepgram

    assert deepgram is not None


def test_version():
    """Test that version is defined."""
    import strands_deepgram

    assert hasattr(strands_deepgram, "__version__")
    assert strands_deepgram.__version__ == "0.1.0"


def test_tool_has_required_attributes():
    """Test that deepgram tool has required attributes."""
    from strands_deepgram import deepgram

    # Check that it's a tool with a name
    assert hasattr(deepgram, "name")
    assert isinstance(deepgram.name, str)
    assert len(deepgram.name) > 0

