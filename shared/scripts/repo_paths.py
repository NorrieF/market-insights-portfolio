from __future__ import annotations
from pathlib import Path


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
