# Knowledge GraphRAG MCP Server

A local-first **Model Context Protocol (MCP)** server that watches a knowledge repository, extracts entities and relations, embeds content with EmbeddingGemma, and serves hybrid (graph + vector) retrieval tools to MCP clients.

- **Local pipeline:** directory watcher → normalization → chunking → entity & relation extraction → sqlite-vec vectorization → graph storage
- **Knowledge graph:** canonical entities, mentions, and typed relations navigated via the bundled `bfsvtab` breadth-first search extension
- **Hybrid retrieval:** semantic vector prefiltering paired with graph expansion and provenance-rich responses

All native dependencies ship with the Python package—no external services or manual compilation required.

## Feature Overview

| Area | Highlights |
| --- | --- |
| Document ingestion | Markdown/HTML/txt normalization, deduplication, preludes for provenance |
| Entity understanding | Mention extraction, canonical linking, relation inference (`uses`, `depends_on`, `defines`, `cites`, …) |
| Storage | SQLite with WAL, `sqlite-vec` for vectors, `bfsvtab` for graph traversal |
| Retrieval tools | Vector + graph search, entity lookup/explain, ingestion/refresh controls, status reporting |
| Local-first | EmbeddingGemma model runs locally (or via optional remote endpoint) |

## Quick Start with `uvx`

The published wheel already includes the native SQLite extensions. You can run the CLI without cloning the repository:

```bash
# Inspect available commands
uvx knowledge-graphrag-mcp --help

# Initialize the database and report status
uvx knowledge-graphrag-mcp status --config config.yaml

# Ingest Markdown files inside a knowledge directory
uvx knowledge-graphrag-mcp ingest ./knowledge/**/*.md --config config.yaml

# Issue a hybrid retrieval query
uvx knowledge-graphrag-mcp hybrid-query "data retention policy" --config config.yaml
```

### Minimal configuration (`config.yaml`)

```yaml
project: "knowledge-graphrag"
sqlite:
  path: "./data/graphrag.sqlite"
embed:
  model: "embedding-gemma-512"
```

Environment overrides:

- `EMBEDDING_GEMMA_MODEL_PATH` – absolute path to a downloaded EmbeddingGemma snapshot (e.g., Hugging Face cache)
- `EMBEDDING_GEMMA_ENDPOINT` – remote embedding service URL; skips local model loading
- `EMBEDDING_GEMMA_STUB=1` – development stub that returns zero vectors (for pipeline smoke tests without the model)

### Install via pip (optional)

```bash
python -m venv .venv
source .venv/bin/activate
pip install knowledge-graph-rag-mcp
knowledge-graphrag-mcp status --config config.yaml
```

## MCP Integration

Add the server to your MCP client configuration (e.g., Claude Desktop) and forward any required environment variables:

```json
{
  "mcpServers": {
    "knowledge-graphrag": {
      "command": "uvx",
      "args": [
        "knowledge-graphrag-mcp",
        "serve",
        "--config",
        "/path/to/config.yaml"
      ],
      "env": {
        "EMBEDDING_GEMMA_MODEL_PATH": "/models/embedding-gemma-300m"
      }
    }
  }
}
```

### Available MCP tools

| Tool | Purpose |
| --- | --- |
| `ingest_docs` | Queue new/changed files for ingestion |
| `extract_and_link` | Run entity & relation extraction for pending docs |
| `hybrid_query` | Graph + vector retrieval with relation filters and hop limits |
| `entity_lookup` | Search canonical entities by name/type |
| `explain_entity` | Summarize entity definitions, aliases, relations, provenance |
| `status` | Report ingest queue depth, table counts, last processed file, error state |

## Data Model

| Table | Description |
| --- | --- |
| `docs` | Source documents with metadata (path, mtime, provenance) |
| `chunks` | Normalized text chunks (content, preludes, hash, overlap metadata) |
| `mentions` | Detected entity mentions tied to chunks |
| `entities` | Canonical entities (type, name, norm, aliases, popularity) |
| `relations` | Directed edges between entities (`uses`, `depends_on`, `defines`, `cites`, etc.) |
| `chunk_vec` / `entity_vec` | Vector storage via `sqlite-vec` |

`bfsvtab` exposes a virtual table that enables breadth-first traversal of `relations`, letting `hybrid_query` expand beyond the initial vector hits.

## Development

```bash
# Clone and install in editable mode
pip install -e .

# Run the CLI (uses local extensions from the repo)
PYTHONPATH=src knowledge-graphrag-mcp status --config config.yaml

# Build distribution artifacts (bundles bfsvtab + sqlite-vec)
python -m build
```

Project layout:

```
src/knowledge_graph_rag_mcp/
├── cli/                  # Typer CLI entrypoints
├── config.py             # YAML configuration models & loader
├── db.py                 # SQLite connection helpers + schema creation
├── embeddings.py         # EmbeddingGemma integration (local/remote/stub)
├── ingest.py             # Document ingestion + vector writes
├── retrieval.py          # Hybrid retrieval & BFS helpers
├── server.py             # MCP server bootstrap + handler wiring
└── tools/__init__.py     # MCP tool implementations
vendor/bfsvtab/           # Bundled bfsvtab extension source
```

### Testing ideas

- Ingest a sample document and run `status`/`hybrid_query`
- Verify `sqlite-vec` and `bfsvtab` appear in `pragma_module_list`
- Exercise MCP tools via `uvx knowledge-graphrag-mcp --help`

## Licensing

- **Knowledge GraphRAG MCP server:** MIT License (`LICENSE`)
- **bfsvtab extension:** public-domain blessing from upstream author (see header in `vendor/bfsvtab/bfsvtab.c`)

## Support

Please open GitHub issues for bug reports or feature requests.
