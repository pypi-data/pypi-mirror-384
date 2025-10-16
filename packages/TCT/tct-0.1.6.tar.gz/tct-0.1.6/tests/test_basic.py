"""Basic tests for TCT package."""

import TCT


def test_import():
    """Test that TCT can be imported successfully."""
    assert TCT is not None


def test_basic_functions_exist():
    """Test that key functions are available."""
    assert hasattr(TCT, 'TCT_help')
    assert hasattr(TCT, 'list_functions')
    assert hasattr(TCT, 'get_Translator_APIs')


def test_tct_help_callable():
    """Test that TCT_help function is callable."""
    assert callable(TCT.TCT_help)