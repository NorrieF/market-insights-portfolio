from __future__ import annotations
from pathlib import Path
import duckdb


def script_dir(from_file: str | Path) -> Path:
    p = Path(from_file).resolve()
    return p.parent if p.is_file() else p


def project_dir(from_file: str | Path) -> Path:
    return script_dir(from_file).parent


def sql_dir(from_file: str | Path) -> Path:
    return project_dir(from_file) / "sql"


def read_sql(from_file: str | Path, filename: str) -> str:
    return (sql_dir(from_file) / filename).read_text(encoding="utf-8")


def repo_root(from_file: str | Path) -> Path:
    return project_dir(from_file).parent.parent


def resolve_repo_path(caller_file: str, p: str) -> Path:
    root = repo_root(caller_file)
    path = Path(p)
    return path if path.is_absolute() else (root / path)


def connect_duckdb(caller_file: str, db: str) -> duckdb.DuckDBPyConnection:
    db_path = resolve_repo_path(caller_file, db)
    return duckdb.connect(str(db_path))


def ensure_outpath(caller_file: str, outpath: str) -> Path:
    resolved = resolve_repo_path(caller_file, outpath)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved