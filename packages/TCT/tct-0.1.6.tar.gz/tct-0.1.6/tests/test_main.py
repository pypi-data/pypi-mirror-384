"""Simple tests for main.py MCP server entry point."""

import inspect


def test_main_entry_point_exists():
    """Test that main.py has the entry point function."""
    import main
    
    assert hasattr(main, 'main')
    assert callable(main.main)


def test_main_imports_mcp_server():
    """Test that main.py imports the MCP server for orchestrating agent access."""
    import main
    
    assert hasattr(main, 'mcp')
    assert main.mcp is not None


def test_main_function_simple():
    """Test that main() function is simple wrapper."""
    import main
    
    # Should be a simple function with no parameters
    sig = inspect.signature(main.main)
    assert len(sig.parameters) == 0
    
    # Should have proper docstring
    assert main.main.__doc__ is not None
    assert "Entry point" in main.main.__doc__