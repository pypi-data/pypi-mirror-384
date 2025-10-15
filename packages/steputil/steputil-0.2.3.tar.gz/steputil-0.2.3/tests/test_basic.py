"""Basic tests for your package."""

import steputil


def test_version():
    """Test that the package version is defined."""
    assert hasattr(steputil, "__version__")
    assert isinstance(steputil.__version__, str)


def test_info():
    """Test the info function."""
    result = steputil.info()
    expected = (
        "steputil - Utilities for building pipeline steps with "
        "configurable command-line argument parsing for JSONL "
        "input/output files"
    )
    assert result == expected
    assert isinstance(result, str)
