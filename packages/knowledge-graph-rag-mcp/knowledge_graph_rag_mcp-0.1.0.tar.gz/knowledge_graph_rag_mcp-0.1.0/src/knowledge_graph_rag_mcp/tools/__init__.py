"""MCP tool handlers for the Knowledge GraphRAG server."""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

from ..embeddings import EmbeddingClient
from ..ingest import ingest_paths
from ..retrieval import run_hybrid_query

LOGGER = logging.getLogger(__name__)


@dataclass
class IngestResult:
    ingested: int
    skipped: int
    errors: List[str]


@dataclass
class ExtractResult:
    mentions: int
    entities_new: int
    relations: int


@dataclass
class HybridQueryResult:
    chunks: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    explanations: List[str]


class ToolHandlers:
    """Container for MCP tool implementations."""

    def __init__(self, connection: sqlite3.Connection, embedder: EmbeddingClient):
        self.connection = connection
        self.embedder = embedder

    def ingest_docs(self, paths: Iterable[str], tags: Optional[List[str]] = None, skip_if_seen: bool = True) -> Dict[str, Any]:
        path_list = list(paths)
        LOGGER.info("Ingesting %s paths", len(path_list))
        ingested, skipped, errors = ingest_paths(
            self.connection,
            path_list,
            embedder=self.embedder,
            skip_if_seen=skip_if_seen,
            tags=tags,
        )
        return asdict(IngestResult(ingested=ingested, skipped=skipped, errors=errors))

    def extract_and_link(self, doc_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        LOGGER.info("extract_and_link invoked (doc_ids=%s)", doc_ids)
        # Extraction pipeline not yet implemented.
        return asdict(ExtractResult(mentions=0, entities_new=0, relations=0))

    def hybrid_query(self, query: str, k: int, hops: int, rels: List[str]) -> Dict[str, Any]:
        LOGGER.info("Running hybrid query '%s'", query)
        result = run_hybrid_query(self.connection, query=query, k=k, hops=hops, rels=rels)
        return asdict(
            HybridQueryResult(
                chunks=result.get("chunks", []),
                entities=result.get("entities", []),
                edges=result.get("edges", []),
                explanations=result.get("explanations", []),
            )
        )

    def entity_lookup(self, q: str, type_filter: Optional[str] = None) -> Dict[str, Any]:
        LOGGER.info("entity_lookup for '%s' (type=%s)", q, type_filter)
        params: List[Any] = [f"%{q}%"]
        where = "name LIKE ?"
        if type_filter:
            where += " AND type = ?"
            params.append(type_filter)
        cur = self.connection.execute(
            f"SELECT id, name, type, meta FROM entities WHERE {where} ORDER BY id LIMIT 20",
            params,
        )
        entities = []
        for row in cur.fetchall():
            meta = json.loads(row["meta"]) if row["meta"] else {}
            entities.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["type"],
                    "meta": meta,
                    "score": 0.0,
                }
            )
        return {"entities": entities}

    def explain_entity(self, entity_id: int, hops: int = 1) -> Dict[str, Any]:
        LOGGER.info("explain_entity id=%s hops=%s", entity_id, hops)
        cur = self.connection.execute("SELECT name, type, meta FROM entities WHERE id = ?", (entity_id,))
        row = cur.fetchone()
        if not row:
            return {"error": f"Entity {entity_id} not found"}
        meta = json.loads(row["meta"]) if row["meta"] else {}
        return {
            "entity": {
                "id": entity_id,
                "name": row["name"],
                "type": row["type"],
                "meta": meta,
            },
            "relations": [],
            "hops": hops,
        }

    def status(self) -> Dict[str, Any]:
        LOGGER.debug("status invoked")
        counts = {}
        for table in ("docs", "chunks", "entities", "relations", "mentions"):
            cur = self.connection.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
            counts[table] = cur.fetchone()["cnt"]
        return {
            "counts": counts,
        }
