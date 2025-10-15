"""Minimal document ingestion pipeline for the Knowledge GraphRAG MCP server."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from array import array
from pathlib import Path
from typing import Iterable, List, Optional

from .embeddings import EmbeddingClient

LOGGER = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".md", ".txt", ".html"}


try:  # Optional helper if sqlite-vec is installed
    from sqlite_vec import serialize_float32 as _vec_serialize_float32  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    _vec_serialize_float32 = None


def _has_table(con: sqlite3.Connection, table: str) -> bool:
    cur = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (table,),
    )
    return cur.fetchone() is not None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _vector_blob(vector: List[float]) -> bytes:
    if _vec_serialize_float32 is not None:
        return _vec_serialize_float32(vector)
    # Fallback: pack as float32 bytes via array
    arr = array("f", vector)
    return arr.tobytes()


def ingest_paths(
    con: sqlite3.Connection,
    paths: Iterable[str],
    embedder: EmbeddingClient,
    skip_if_seen: bool = True,
    tags: Optional[List[str]] = None,
) -> tuple[int, int, List[str]]:
    """Ingest the provided paths into SQLite using a simplistic pipeline."""

    tags = tags or []
    ingested = 0
    skipped = 0
    errors: List[str] = []

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            msg = f"Path not found: {path}"
            LOGGER.warning(msg)
            errors.append(msg)
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            LOGGER.info("Skipping unsupported file %s", path)
            skipped += 1
            continue

        stat = path.stat()
        mtime_ms = int(stat.st_mtime * 1000)
        text = _read_text(path)
        content_hash = _hash_text(text)

        cur = con.execute("SELECT id, mtime_ms, meta FROM docs WHERE path = ?", (str(path),))
        row = cur.fetchone()
        if row and skip_if_seen:
            row_meta = json.loads(row["meta"]) if row["meta"] else {}
            row_hash = row_meta.get("hash")
            if row["mtime_ms"] == mtime_ms and row_hash == content_hash:
                LOGGER.debug("Skipping unchanged file %s", path)
                skipped += 1
                continue

        doc_meta = {
            "tags": tags,
            "hash": content_hash,
            "size": stat.st_size,
        }

        chunk_meta = {
            "prelude": f"{path} • full",
            "lang": "en",
            "hash": content_hash,
        }

        vector: List[float] | None = None
        embed_input = f"{chunk_meta['prelude']}\n{text}"
        try:
            vector = embedder.embed_many([embed_input])[0]
        except Exception as exc:  # pragma: no cover - runtime dependency/remote failure
            LOGGER.error("Embedding failed for %s: %s", path, exc)
            errors.append(f"embedding_failed:{path}")
            vector = None

        has_chunk_vec = _has_table(con, "chunk_vec")
        if not has_chunk_vec:
            raise RuntimeError(
                "sqlite-vec tables not initialized; ensure the MCP server loads the sqlite-vec extension."
            )

        with con:
            if row:
                doc_id = row["id"]
                LOGGER.debug("Updating doc %s (id=%s)", path, doc_id)
                con.execute(
                    "UPDATE docs SET source = ?, mtime_ms = ?, meta = ? WHERE id = ?",
                    ("local", mtime_ms, json.dumps(doc_meta), doc_id),
                )
                if has_chunk_vec:
                    try:
                        con.execute(
                            """
                            DELETE FROM chunk_vec
                            WHERE rowid IN (
                                SELECT rowid FROM chunk_vec_map
                                WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_id = ?)
                            )
                            """,
                            (doc_id,),
                        )
                        con.execute(
                            "DELETE FROM chunk_vec_map WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_id = ?)",
                            (doc_id,),
                        )
                    except sqlite3.DatabaseError as exc:
                        LOGGER.debug("Skipping vector cleanup for %s (%s)", path, exc)
                con.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            else:
                LOGGER.debug("Inserting doc %s", path)
                cur = con.execute(
                    "INSERT INTO docs(path, source, mtime_ms, meta) VALUES (?, ?, ?, ?)",
                    (str(path), "local", mtime_ms, json.dumps(doc_meta)),
                )
                doc_id = cur.lastrowid

            cur = con.execute(
                "INSERT INTO chunks(doc_id, content, meta) VALUES (?, ?, ?)",
                (doc_id, text, json.dumps(chunk_meta)),
            )
            chunk_id = cur.lastrowid

            if vector:
                try:
                    con.execute(
                        "INSERT INTO chunk_vec(rowid, vector) VALUES (?, ?)",
                        (chunk_id, _vector_blob(vector)),
                    )
                    con.execute(
                        "INSERT OR REPLACE INTO chunk_vec_map(chunk_id, rowid) VALUES (?, ?)",
                        (chunk_id, chunk_id),
                    )
                except sqlite3.DatabaseError as exc:
                    LOGGER.debug("Skipping vector insert for %s (%s)", path, exc)

        ingested += 1

    return ingested, skipped, errors
