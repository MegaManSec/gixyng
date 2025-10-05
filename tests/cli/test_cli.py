"""
Module: test_cli.py

This module demonstrates how to test the pixy's CLI using pytest.
"""

import sys
import pytest
from gixy.cli.main import main, _get_cli_parser


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


def test_cli_vars_dirs_option_present():
    parser = _get_cli_parser()
    args = parser.parse_args(["--vars-dirs", "/etc/gixy/vars", "-"])
    # ensure option parsed
    assert getattr(args, "vars_dirs", None) == "/etc/gixy/vars"


def test_cli_help_contains_cta(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["gixy", "--help"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "nginx-extras.getpagespeed.com" in captured.out
