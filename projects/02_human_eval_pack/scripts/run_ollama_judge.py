from __future__ import annotations

import argparse
import json
import re
import time
from typing import Any, Dict, List, Tuple

import requests
from tqdm import tqdm

from shared.scripts.repo_paths import read_sql, connect_duckdb


Row = Tuple[int, str, str, str]  # slot, doc_id, title, text


OLLAMA_URL = "http://localhost:11434/api/generate"


def clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n].rstrip() + "…"


def build_prompt(query_text: str, n_rel: int, rows: List[Row], text_chars: int) -> str:
    lines: List[str] = []
    for slot, _doc_id, title, text in rows:
        title = (title or "").strip()
        text = clip(text or "", text_chars)
        lines.append(f"{slot}. {title}\n   {text}")

    return (
        "You are judging relevance between a scientific claim and paper abstracts.\n\n"
        f"CLAIM (query): {query_text}\n\n"
        f"Exactly {n_rel} of the following {len(rows)} documents are relevant.\n"
        "Return ONLY a JSON object of the form:\n"
        '{"slots":[2,5]}\n'
        f"Rules:\n"
        f"- slots must be integers between 1 and {len(rows)}\n"
        f"- output exactly {n_rel} unique slots\n\n"
        "DOCUMENTS:\n"
        + "\n\n".join(lines)
        + "\n"
    )


def parse_slots_loose(out: str, topk: int, n_rel: int) -> List[int]:
    """
    Robust parsing even if the model returns invalid JSON like {"slots":[1,]}.
    Strategy: extract integers, dedupe, clamp to 1..topk, then force exactly n_rel.
    """
    nums = [int(x) for x in re.findall(r"\d+", out)]
    slots: List[int] = []
    seen = set()
    for x in nums:
        if 1 <= x <= topk and x not in seen:
            slots.append(x)
            seen.add(x)

    if len(slots) < n_rel:
        for x in range(1, topk + 1):
            if x not in seen:
                slots.append(x)
                seen.add(x)
            if len(slots) == n_rel:
                break

    return slots[:n_rel]


def ollama_pick_slots(model: str, prompt: str) -> List[int]:
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
        "keep_alive": "5m",
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    out = (data.get("response") or "").strip()

    # Try strict JSON first
    try:
        obj = json.loads(out)
        slots = obj.get("slots", [])
        slots = [int(s) for s in slots]
        return slots
    except Exception:
        # Fall back to loose parsing
        return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt-v", default="v1")
    ap.add_argument("--text-chars", type=int, default=600, help="Max chars of abstract text per doc in prompt")
    ap.add_argument("--sleep", type=float, default=0.02, help="Small pause per query to reduce load")
    args = ap.parse_args()

    con = connect_duckdb(__file__, args.db)

    con.execute(read_sql(__file__, "schema_ollama.sql"))
    con.execute("DELETE FROM ollama_picks WHERE model = ? AND prompt_v = ?", [args.model, args.prompt_v])

    qids = [
        r[0]
        for r in con.execute(
            "SELECT DISTINCT query_id FROM judge_items_for_llm ORDER BY CAST(query_id AS INTEGER)"
        ).fetchall()
    ]

    for qid in tqdm(qids, desc="ollama judging"):
        query_text, n_rel = con.execute(
            """
            SELECT query_text, n_rel
            FROM judge_items_for_llm
            WHERE query_id = ?
            LIMIT 1
            """,
            [qid],
        ).fetchone()

        rows: List[Row] = con.execute(
            """
            SELECT slot, doc_id, title, text
            FROM judge_items_for_llm
            WHERE query_id = ?
            ORDER BY slot
            """,
            [qid],
        ).fetchall()

        topk = len(rows)
        prompt = build_prompt(query_text, int(n_rel), rows, args.text_chars)

        slots = ollama_pick_slots(args.model, prompt)
        slots = parse_slots_loose(str({"slots": slots}), topk=topk, n_rel=int(n_rel))

        slot_to_doc = {slot: doc_id for slot, doc_id, _title, _text in rows}

        inserts = [(qid, s, slot_to_doc[s], args.model, args.prompt_v) for s in slots]
        con.executemany(
            "INSERT INTO ollama_picks(query_id, slot, doc_id, model, prompt_v) VALUES (?, ?, ?, ?, ?)",
            inserts,
        )

        if args.sleep:
            time.sleep(args.sleep)

    n = con.execute(
        "SELECT COUNT(*) FROM ollama_picks WHERE model = ? AND prompt_v = ?",
        [args.model, args.prompt_v],
    ).fetchone()[0]
    print(f"Done. ollama_picks={n:,} model={args.model} prompt_v={args.prompt_v} db={db_path}")

    con.execute("CHECKPOINT;")
    con.close()


if __name__ == "__main__":
    main()
