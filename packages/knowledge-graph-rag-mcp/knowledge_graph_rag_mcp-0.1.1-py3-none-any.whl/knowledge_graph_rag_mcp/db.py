"""SQLite helpers and schema management."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

try:  # Optional dependency for bundled sqlite-vec extension
    import sqlite_vec  # type: ignore
except ImportError:  # pragma: no cover - the package is optional
    sqlite_vec = None  # type: ignore

LOGGER = logging.getLogger(__name__)

_PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
    "PRAGMA busy_timeout=3000;",
)


_SCHEMA = """
-- Documents
CREATE TABLE IF NOT EXISTS docs (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  source TEXT,
  mtime_ms INTEGER,
  meta JSON
);
CREATE INDEX IF NOT EXISTS idx_docs_path ON docs(path);

-- Chunks
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY,
  doc_id INTEGER REFERENCES docs(id) ON DELETE CASCADE,
  content TEXT,
  meta JSON
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

-- Entities
CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY,
  type TEXT,
  name TEXT,
  norm TEXT,
  meta JSON,
  status TEXT DEFAULT 'active'
);
CREATE INDEX IF NOT EXISTS idx_entities_norm ON entities(norm);
CREATE INDEX IF NOT EXISTS idx_entities_type_name ON entities(type, name);

-- Mentions
CREATE TABLE IF NOT EXISTS mentions (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NULL REFERENCES entities(id) ON DELETE SET NULL,
  doc_id INTEGER REFERENCES docs(id) ON DELETE CASCADE,
  chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
  span_start INTEGER,
  span_end INTEGER,
  surface TEXT,
  type TEXT,
  meta JSON
);
CREATE INDEX IF NOT EXISTS idx_mentions_doc ON mentions(doc_id);
CREATE INDEX IF NOT EXISTS idx_mentions_entity ON mentions(entity_id);

-- Relations
CREATE TABLE IF NOT EXISTS relations (
  src_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
  dst_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
  rel TEXT,
  meta JSON,
  PRIMARY KEY (src_id, dst_id, rel)
);
CREATE INDEX IF NOT EXISTS idx_rel_src_rel ON relations(src_id, rel);
CREATE INDEX IF NOT EXISTS idx_rel_dst_rel ON relations(dst_id, rel);

-- Vector maps (sqlite-vec virtual tables created separately)
CREATE TABLE IF NOT EXISTS chunk_vec_map (
  chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
  rowid INTEGER UNIQUE
);

CREATE TABLE IF NOT EXISTS entity_vec_map (
  entity_id INTEGER PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
  rowid INTEGER UNIQUE
);

CREATE VIEW IF NOT EXISTS graph_edges AS
  SELECT src_id AS src, dst_id AS dst FROM relations;
"""


def open_connection(path: Path, load_extensions: Optional[Iterable[Path]] = None) -> sqlite3.Connection:
    """Open a SQLite connection with the expected pragmas applied."""

    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    for pragma in _PRAGMAS:
        con.execute(pragma)
    if load_extensions:
        con.enable_load_extension(True)
        for extension in load_extensions:
            LOGGER.info("Loading SQLite extension %s", extension)
            con.load_extension(str(extension))
        con.enable_load_extension(False)
    if sqlite_vec is not None:
        con.enable_load_extension(True)
        try:
            sqlite_vec.load(con)  # type: ignore[attr-defined]
            LOGGER.debug("sqlite-vec extension loaded via python package")
        except Exception as exc:  # pragma: no cover - environment specific
            LOGGER.warning("Failed to load sqlite-vec via package: %s", exc)
        finally:
            con.enable_load_extension(False)
    return con


def ensure_schema(con: sqlite3.Connection) -> None:
    """Create tables and views if they are missing."""

    LOGGER.debug("Ensuring SQLite schema is up to date")
    con.executescript(_SCHEMA)


def has_vec_module(con: sqlite3.Connection) -> bool:
    """Return True if the sqlite-vec module is available in this connection."""

    try:
        cur = con.execute("SELECT 1 FROM pragma_module_list WHERE name = 'vec0'")
        return cur.fetchone() is not None
    except sqlite3.DatabaseError:  # pragma: no cover - pragma not available
        return False


def ensure_vector_tables(con: sqlite3.Connection, dim: int = 512) -> None:
    """Create sqlite-vec virtual tables once the extension is available."""

    if not has_vec_module(con):
        raise RuntimeError(
            "sqlite-vec extension is not available; install the 'sqlite-vec' package or "
            "provide a loadable module path via configuration."
        )

    LOGGER.debug("Ensuring sqlite-vec virtual tables exist (dim=%s)", dim)
    con.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vec USING vec0(vector FLOAT[{dim}]);"
    )
    con.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS entity_vec USING vec0(vector FLOAT[{dim}]);"
    )
