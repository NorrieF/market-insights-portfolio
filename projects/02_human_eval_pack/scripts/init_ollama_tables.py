from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from shared.scripts.repo_paths import repo_root, read_sql


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    args = ap.parse_args()

    root = repo_root(__file__)
    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = root / db_path

    con = duckdb.connect(str(db_path))
    con.execute(read_sql(__file__, "schema_ollama.sql"))
    con.execute("CHECKPOINT;")
    con.close()

    print(f"Done. Initialized ollama tables in {db_path}")


if __name__ == "__main__":
    main()
