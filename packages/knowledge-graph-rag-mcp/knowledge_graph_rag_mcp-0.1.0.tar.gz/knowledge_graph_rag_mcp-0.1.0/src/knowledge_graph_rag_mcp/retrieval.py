"""Hybrid retrieval scaffolding (placeholder implementation)."""

from __future__ import annotations

import logging
import sqlite3
from typing import Dict, Iterable, List, Set, Tuple

LOGGER = logging.getLogger(__name__)


def _find_seed_entities(con: sqlite3.Connection, query: str, limit: int = 5) -> List[Tuple[int, str, str]]:
    cur = con.execute(
        "SELECT id, name, type FROM entities WHERE name LIKE ? ORDER BY id LIMIT ?",
        (f"%{query}%", limit),
    )
    return [(row["id"], row["name"], row["type"] or "") for row in cur.fetchall()]


def _bfs_nodes(con: sqlite3.Connection, roots: Iterable[int], hops: int) -> Dict[int, List[Dict[str, int]]]:
    results: Dict[int, List[Dict[str, int]]] = {}
    for root in roots:
        try:
            cur = con.execute(
                """
                SELECT id, distance, parent
                FROM bfsvtab
                WHERE tablename = ?
                  AND fromcolumn = ?
                  AND tocolumn = ?
                  AND root = ?
                  AND distance <= ?
                """,
                ("graph_edges", "src", "dst", root, hops),
            )
        except sqlite3.OperationalError as exc:
            LOGGER.warning("bfsvtab query failed: %s", exc)
            continue
        rows = cur.fetchall()
        if rows:
            results[root] = [
                {"id": row["id"], "distance": row["distance"], "parent": row["parent"]}
                for row in rows
            ]
    return results


def _entities_for_ids(con: sqlite3.Connection, ids: Iterable[int]) -> List[Dict[str, object]]:
    ids = list({i for i in ids if i is not None})
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    cur = con.execute(
        f"SELECT id, name, type, meta FROM entities WHERE id IN ({placeholders})",
        ids,
    )
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "meta": row["meta"],
        }
        for row in cur.fetchall()
    ]


def _relation_edges(
    con: sqlite3.Connection,
    node_ids: Set[int],
    rels: List[str],
) -> List[Dict[str, object]]:
    if not node_ids:
        return []
    node_list = list(node_ids)
    node_placeholders = ",".join("?" for _ in node_list)
    params: List[object] = node_list + node_list
    rel_filter = ""
    if rels:
        rel_placeholders = ",".join("?" for _ in rels)
        rel_filter = f" AND rel IN ({rel_placeholders})"
        params.extend(rels)
    cur = con.execute(
        f"""
        SELECT src_id, dst_id, rel
        FROM relations
        WHERE src_id IN ({node_placeholders})
          AND dst_id IN ({node_placeholders})
          {rel_filter}
        """,
        params,
    )
    return [
        {"src": row["src_id"], "dst": row["dst_id"], "rel": row["rel"]}
        for row in cur.fetchall()
    ]


def run_hybrid_query(
    con: sqlite3.Connection,
    query: str,
    k: int,
    hops: int,
    rels: List[str],
) -> Dict[str, List[Dict]]:
    """Return a naive semantic search result for bootstrapping purposes."""

    _ = (hops, rels)
    wildcard = f"%{query}%"
    cur = con.execute(
        """
        SELECT c.id, c.content, c.meta, d.id as doc_id, d.path
        FROM chunks c
        JOIN docs d ON d.id = c.doc_id
        WHERE c.content LIKE ?
        ORDER BY c.id DESC
        LIMIT ?
        """,
        (wildcard, k),
    )

    chunks: List[Dict] = []
    for row in cur.fetchall():
        chunks.append(
            {
                "id": row["id"],
                "doc_id": row["doc_id"],
                "snippet": row["content"][:400],
                "path": row["path"],
                "meta": row["meta"],
            }
        )

    seeds = _find_seed_entities(con, query)
    bfs_map = _bfs_nodes(con, (seed[0] for seed in seeds), hops)
    node_ids: Set[int] = {seed_id for seed_id, *_ in seeds}
    for expansions in bfs_map.values():
        node_ids.update(node["id"] for node in expansions)
    entity_details = _entities_for_ids(con, node_ids)
    edges = _relation_edges(con, node_ids, rels)

    explanation = "content LIKE match"
    if bfs_map:
        explanation = f"{explanation} + {len(bfs_map)} bfs roots"

    LOGGER.debug(
        "Hybrid query '%s' returned %s chunks and %s entity nodes", query, len(chunks), len(entity_details)
    )
    return {
        "chunks": chunks,
        "entities": entity_details,
        "edges": edges,
        "explanations": [explanation],
    }
