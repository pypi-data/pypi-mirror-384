#!/usr/bin/env python3
"""
Entry point for running mem8 CLI as a module (python -m mem8.cli).
"""

from .utils import setup_utf8_encoding
from .main import typer_app

if __name__ == "__main__":
    setup_utf8_encoding()
    typer_app()
