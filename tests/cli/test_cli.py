"""
Module: test_cli.py

This module demonstrates how to test the pixy's CLI using pytest.
"""

import sys
import pytest
from gixy.cli.main import main


def test_cli_help(monkeypatch, capsys):
    """
    Test that running the CLI with --help displays usage information.
    """
    # Set sys.argv to simulate "pixy --help"
    monkeypatch.setattr(sys, "argv", ["pixy", "--help"])

    # If the CLI prints help and then exits, SystemExit is expected.
    with pytest.raises(SystemExit) as e:
        main()

    # Optionally check exit code (commonly 0 for --help)
    assert e.value.code == 0

    # Capture and check the output for expected help text.
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()
