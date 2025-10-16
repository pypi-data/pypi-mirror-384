#!/usr/bin/env python3
"""
Application state management for mem8 CLI.
"""

from typing import Optional
from pathlib import Path

from ..core.config import Config
from ..core.memory import MemoryManager
from ..core.sync import SyncManager
from ..core.intelligent_query import IntelligentQueryEngine
from ..core.thought_actions import ThoughtActionEngine
from ..core.utils import setup_logging

from .utils import get_console

# Create console instance for error handling
console = get_console()


class AppState:
    """Centralized application state with lazy initialization."""

    def __init__(self):
        self._config = None
        self._memory_manager = None
        self._sync_manager = None
        self._query_engine = None
        self._action_engine = None
        self._initialized = False

    def initialize(self, verbose: bool = False, config_dir: Optional[Path] = None):
        """Initialize state with parameters. Only initializes once."""
        if self._initialized:
            return  # Already initialized, skip re-initialization

        if verbose:
            setup_logging(True)

        # Initialize components
        self._config = Config(config_dir)
        self._memory_manager = MemoryManager(self._config)
        self._sync_manager = SyncManager(self._config)
        self._query_engine = IntelligentQueryEngine(self._memory_manager.thought_discovery)
        self._action_engine = ThoughtActionEngine(self._config)
        self._initialized = True

    @property
    def config(self) -> Config:
        if not self._config:
            self.initialize()
        return self._config

    @property
    def memory_manager(self) -> MemoryManager:
        if not self._memory_manager:
            self.initialize()
        return self._memory_manager

    @property
    def sync_manager(self) -> SyncManager:
        if not self._sync_manager:
            self.initialize()
        return self._sync_manager

    @property
    def query_engine(self) -> IntelligentQueryEngine:
        if not self._query_engine:
            self.initialize()
        return self._query_engine

    @property
    def action_engine(self) -> ThoughtActionEngine:
        if not self._action_engine:
            self.initialize()
        return self._action_engine


# Global app state instance
app_state = AppState()


def get_state() -> AppState:
    """Dependency injection helper for accessing app state."""
    return app_state


# Dependency injection helpers
def get_memory_manager() -> MemoryManager:
    """Get memory manager instance."""
    return app_state.memory_manager


def get_query_engine() -> IntelligentQueryEngine:
    """Get query engine instance."""
    return app_state.query_engine


def get_action_engine() -> ThoughtActionEngine:
    """Get action engine instance."""
    return app_state.action_engine


def get_sync_manager() -> SyncManager:
    """Get sync manager instance."""
    return app_state.sync_manager


def get_config() -> Config:
    """Get configuration instance."""
    return app_state.config


def set_app_state(verbose: bool = False, config_dir: Optional[Path] = None):
    """Initialize app state with parameters."""
    app_state.initialize(verbose=verbose, config_dir=config_dir)


def handle_command_error(e: Exception, verbose: bool, context: str = "command") -> None:
    """Standardized error handling for all commands."""
    console.print(f"❌ [bold red]Error during {context}: {e}[/bold red]")
    if verbose:
        console.print_exception()
