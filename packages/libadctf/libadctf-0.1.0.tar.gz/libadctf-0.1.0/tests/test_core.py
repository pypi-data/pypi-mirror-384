"""
Tests for libadctf library
"""

import pytest
from libadctf.core import main, hello_world


def test_main():
    """Test the main function"""
    result = main()
    assert result == "Library is working!"


def test_hello_world():
    """Test the hello_world function"""
    result = hello_world()
    assert result == "Hello World from libadctf!"
    assert isinstance(result, str)


def test_main_output(capsys):
    """Test that main function prints expected output"""
    main()
    captured = capsys.readouterr()
    assert "Hello from libadctf!" in captured.out