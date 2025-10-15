# Knowledge GraphRAG MCP Server

This module hosts the local-first Knowledge GraphRAG MCP server defined in `../docs/knowledge-graph-rag-mcp.md`. The spec outlines the document watcher/normalizer pipeline, entity & relation extraction, EmbeddingGemma vectorization, SQLite (`sqlite-vec`, `bfsvtab`) storage, and the MCP tool surface for retrieval and maintenance.

## Next Steps
- Break down the spec into implementation milestones (schema, normalizers, extraction/linking, retrieval).
- Scaffold the codebase (`src/`, `tests/`, configuration) aligned with the deliverables checklist.

Review the spec for architecture diagrams, pseudo-code, and validation guidance.

## Packaging

The project is published as a Python package with a bundled copy of the `bfsvtab`
SQLite extension. Local builds automatically compile the shared library when
`pip` installs the project. To produce distribution artifacts:

```bash
python -m build
```

The build step generates `dist/*.whl` and `dist/*.tar.gz` artifacts that embed
`bfsvtab` alongside the Python modules, so downstream users do not need to
compile extensions manually.
