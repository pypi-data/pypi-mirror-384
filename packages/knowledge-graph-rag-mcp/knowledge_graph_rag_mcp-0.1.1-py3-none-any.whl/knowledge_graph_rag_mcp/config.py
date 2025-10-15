"""Configuration loading for the Knowledge GraphRAG MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from importlib import resources

import yaml


_DEFAULT_REGEX = r"v?\d+\.\d+(\.\d+)?(-[a-z0-9]+)?"
_DEFAULT_RELS = ["defines", "depends_on", "uses", "cites"]
_DEFAULT_WEIGHTS = {"semantic": 0.7, "graph": 0.3}
def _default_bfsvtab_path() -> Optional[Path]:
    for candidate_name in ("bfsvtab.so", "bfsvtab.dll"):
        try:
            bfsvtab_file = resources.files("knowledge_graph_rag_mcp.native").joinpath(candidate_name)
            with resources.as_file(bfsvtab_file) as local_path:
                if local_path.exists():
                    return local_path
        except (FileNotFoundError, ModuleNotFoundError):
            continue

    root_dir = Path(__file__).resolve().parent.parent.parent
    for fallback_name in ("bfsvtab.so", "bfsvtab.dll"):
        candidate = root_dir / "vendor" / "bfsvtab" / fallback_name
        if candidate.exists():
            return candidate
    return None


@dataclass
class ExtractConfig:
    ner: str = "spacy:en_core_web_sm"
    gazetteer_mine_topk: int = 2000
    gazetteer_min_freq: int = 3
    regex_version: str = _DEFAULT_REGEX


@dataclass
class EmbedConfig:
    model: str = "embedding-gemma-512"
    dim: int = 512
    quantize: int = 8
    remote: Optional[str] = None


@dataclass
class RetrievalConfig:
    k: int = 40
    hops: int = 2
    rels: List[str] = field(default_factory=lambda: list(_DEFAULT_RELS))
    weights: Dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_WEIGHTS))


@dataclass
class SQLiteConfig:
    path: Path = Path("./data/graphrag.sqlite")
    wal: bool = True
    extensions_dir: Optional[Path] = None
    sqlite_vec: Optional[Path] = None
    bfsvtab: Optional[Path] = None

    def extension_paths(self) -> List[Path]:
        paths: List[Path] = []
        for raw in (self.sqlite_vec, self.bfsvtab):
            if raw:
                paths.append(Path(raw).expanduser().resolve())
        if self.bfsvtab is None:
            default = _default_bfsvtab_path()
            if default is not None:
                paths.append(default)
        return paths


@dataclass
class WatchConfig:
    dir: Optional[Path] = None
    debounce_ms: int = 300


@dataclass
class ServerConfig:
    project: str = "knowledge-graphrag"
    watch: WatchConfig = field(default_factory=WatchConfig)
    extract: ExtractConfig = field(default_factory=ExtractConfig)
    embed: EmbedConfig = field(default_factory=EmbedConfig)
    sqlite: SQLiteConfig = field(default_factory=SQLiteConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)


def _resolve_path(base: Optional[Path], value: Optional[str]) -> Optional[Path]:
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute() or base is None:
        return candidate.expanduser()
    return (base / candidate).expanduser()


def load_config(path: Path | str | None = None) -> ServerConfig:
    """Load configuration from YAML, falling back to defaults."""

    cfg_path = Path(path) if path else None
    data = {}
    if cfg_path and cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

    watch_data = data.get("watch", {})
    extract_data = data.get("extract", {})
    embed_data = data.get("embed", {})
    sqlite_data = data.get("sqlite", {})
    retrieval_data = data.get("retrieval", {})

    extensions_dir = sqlite_data.get("extensions_dir")
    extensions_dir_path = Path(extensions_dir).expanduser() if extensions_dir else None

    sqlite_cfg = SQLiteConfig(
        path=Path(sqlite_data.get("path", "./data/graphrag.sqlite")),
        wal=sqlite_data.get("wal", True),
        extensions_dir=extensions_dir_path,
        sqlite_vec=_resolve_path(extensions_dir_path, sqlite_data.get("sqlite_vec")),
        bfsvtab=_resolve_path(extensions_dir_path, sqlite_data.get("bfsvtab")),
    )

    return ServerConfig(
        project=data.get("project", "knowledge-graphrag"),
        watch=WatchConfig(
            dir=Path(watch_data["dir"]) if watch_data.get("dir") else None,
            debounce_ms=watch_data.get("debounce_ms", 300),
        ),
        extract=ExtractConfig(
            ner=extract_data.get("ner", "spacy:en_core_web_sm"),
            gazetteer_mine_topk=extract_data.get("gazetteer", {}).get("mine_topk", 2000),
            gazetteer_min_freq=extract_data.get("gazetteer", {}).get("min_freq", 3),
            regex_version=extract_data.get("regex", {}).get("version", _DEFAULT_REGEX),
        ),
        embed=EmbedConfig(
            model=embed_data.get("model", "embedding-gemma-512"),
            dim=embed_data.get("dim", 512),
            quantize=embed_data.get("quantize", 8),
            remote=embed_data.get("remote"),
        ),
        sqlite=sqlite_cfg,
        retrieval=RetrievalConfig(
            k=retrieval_data.get("k", 40),
            hops=retrieval_data.get("hops", 2),
            rels=retrieval_data.get("rels", list(_DEFAULT_RELS)),
            weights=retrieval_data.get("weights", dict(_DEFAULT_WEIGHTS)),
        ),
    )
