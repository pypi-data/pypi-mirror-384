"""Typer application for managing the Knowledge GraphRAG MCP server."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

import typer

from ..config import ServerConfig, load_config
from ..server import MCPServer
from ..tools import ToolHandlers

app = typer.Typer(help="Knowledge GraphRAG MCP server utilities")
logging.basicConfig(level=logging.INFO)


def _start_server(config_path: Path) -> MCPServer:
    config = load_config(config_path)
    server = MCPServer(config)
    server.start()
    return server


@app.command()
def serve(
    config_path: Path = typer.Option(Path("config.yaml"), "--config", "-c", help="Path to configuration file"),
) -> None:
    """Start the MCP server (placeholder)."""

    server = _start_server(config_path)
    typer.echo("Knowledge GraphRAG MCP server started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        typer.echo("Stopping server...")
    finally:
        server.stop()


@app.command()
def ingest(
    paths: List[Path] = typer.Argument(..., help="Paths or glob patterns to ingest"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Optional tags to attach"),
    skip_if_seen: bool = typer.Option(True, help="Skip unchanged documents"),
    config_path: Path = typer.Option(Path("config.yaml"), "--config", "-c", help="Path to configuration file"),
) -> None:
    """Ingest the provided paths using the MCP tool pipeline."""

    server = _start_server(config_path)
    try:
        handlers = ToolHandlers(server.connection, server.embedder)
        result = handlers.ingest_docs([str(p) for p in paths], tags=tags, skip_if_seen=skip_if_seen)
        typer.echo(json.dumps(result, indent=2))
    finally:
        server.stop()


@app.command()
def status(
    config_path: Path = typer.Option(Path("config.yaml"), "--config", "-c", help="Path to configuration file"),
) -> None:
    """Print basic status information."""

    server = _start_server(config_path)
    try:
        handlers = ToolHandlers(server.connection, server.embedder)
        typer.echo(json.dumps(handlers.status(), indent=2))
    finally:
        server.stop()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
