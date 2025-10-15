"""MCP server bootstrap logic."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from .config import ServerConfig, load_config
from .db import ensure_schema, ensure_vector_tables, open_connection
from .embeddings import EmbeddingClient
from .tools import ToolHandlers

LOGGER = logging.getLogger(__name__)


class MCPServer:
    """Placeholder MCP server implementation."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.connection: Optional[sqlite3.Connection] = None
        self.embedder = EmbeddingClient(
            model=config.embed.model,
            dim=config.embed.dim,
            quantize=config.embed.quantize,
            remote_override=config.embed.remote,
        )

    def start(self) -> None:
        """Initialize resources and begin serving (placeholder)."""

        LOGGER.info("Starting Knowledge GraphRAG MCP server for project '%s'", self.config.project)
        extension_paths = self.config.sqlite.extension_paths()
        if extension_paths:
            LOGGER.info("SQLite extensions configured: %s", ", ".join(str(p) for p in extension_paths))
        self.connection = open_connection(self.config.sqlite.path, extension_paths)
        ensure_schema(self.connection)
        try:
            ensure_vector_tables(self.connection, dim=self.config.embed.dim)
            LOGGER.debug("sqlite-vec virtual tables ready")
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("sqlite-vec initialization failed: %s", exc)
            raise
        LOGGER.info("SQLite schema ensured at %s", self.config.sqlite.path)
        # TODO: integrate with MCP framework (context7) once handlers are implemented.

    def stop(self) -> None:
        if self.connection is not None:
            LOGGER.info("Closing SQLite connection")
            self.connection.close()
            self.connection = None

    def get_handlers(self) -> ToolHandlers:
        if not self.connection:
            raise RuntimeError("Server connection not initialized")
        return ToolHandlers(self.connection, self.embedder)


def load_and_start(config_path: Optional[Path] = None) -> MCPServer:
    """Helper that loads configuration and starts the MCP server."""

    config = load_config(config_path)
    server = MCPServer(config)
    server.start()
    return server
