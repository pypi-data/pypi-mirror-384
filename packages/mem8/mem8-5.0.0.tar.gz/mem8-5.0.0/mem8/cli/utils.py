#!/usr/bin/env python3
"""
Shared CLI utilities.
"""

import os
import sys
from rich.console import Console


def setup_utf8_encoding():
    """Setup UTF-8 encoding for Windows compatibility."""
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

    try:
        import colorama
        colorama.init(autoreset=True)
    except ImportError:
        pass


def get_console() -> Console:
    """Get configured Rich console instance."""
    return Console(
        force_terminal=True,
        legacy_windows=None  # Auto-detect Windows compatibility
    )
