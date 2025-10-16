#!/usr/bin/env python3
"""
Entry point for mem8 CLI.
"""

from .cli.utils import setup_utf8_encoding
from .cli.main import typer_app


def main():
    """Entry point for the CLI using Typer."""
    setup_utf8_encoding()
    typer_app()


if __name__ == "__main__":
    main()
