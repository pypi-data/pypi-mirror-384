"""Top-level package for the Knowledge GraphRAG MCP server."""

from importlib import metadata


def __getattr__(name: str):
    if name == "__version__":
        try:
            return metadata.version("knowledge-graph-rag-mcp")
        except metadata.PackageNotFoundError:  # pragma: no cover
            return "0.0.0"
    raise AttributeError(name)
